"""
Reads store/schedule.json and publishes any posts due in the last 65 minutes.
Designed to run on GitHub Actions via hourly cron — not for local use.

Updates draft status in store/drafts/ after publishing so GitHub Actions
can commit the changes back to the repository.

Environment variables (set as GitHub Secrets):
  LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN
  TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN,
  TWITTER_ACCESS_TOKEN_SECRET

Usage:
  python tools/auto_publish.py
"""

import os
import json
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

STORE        = Path("store")
SCHEDULE     = STORE / "schedule.json"
DRAFTS_DIR   = STORE / "drafts"
LINKEDIN_API = "https://api.linkedin.com/v2"


def _load_draft(draft_id: str) -> dict:
    path = DRAFTS_DIR / f"{draft_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Draft '{draft_id}' not found in {DRAFTS_DIR}")
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_draft(draft_id: str, **updates) -> None:
    path = DRAFTS_DIR / f"{draft_id}.json"
    draft = json.loads(path.read_text(encoding="utf-8"))
    draft.update(updates)
    draft["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path.write_text(json.dumps(draft, indent=2), encoding="utf-8")


def _publish_linkedin(draft_id: str) -> dict:
    draft    = _load_draft(draft_id)
    content  = draft.get("content", "")
    if isinstance(content, list):
        content = "\n\n".join(content)
    tags = draft.get("hashtags", [])
    if tags:
        content = f"{content}\n\n{' '.join(t if t.startswith('#') else f'#{t}' for t in tags)}"

    token      = os.environ["LINKEDIN_ACCESS_TOKEN"]
    person_urn = os.environ["LINKEDIN_PERSON_URN"]

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    r = requests.post(f"{LINKEDIN_API}/ugcPosts", headers=headers, json=payload)
    r.raise_for_status()

    post_id  = r.headers.get("x-restli-id") or r.json().get("id", "")
    post_url = f"https://www.linkedin.com/feed/update/{post_id}/"
    _patch_draft(draft_id, status="published",
                 published_at=datetime.now().isoformat(timespec="seconds"),
                 post_id=post_id, post_url=post_url)
    return {"post_id": post_id, "post_url": post_url}


def _publish_twitter(draft_id: str) -> dict:
    try:
        import tweepy
    except ImportError:
        raise ImportError("tweepy required: pip install tweepy")

    draft   = _load_draft(draft_id)
    content = draft.get("content", "")
    tweets  = content if isinstance(content, list) else [content]

    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,
    )
    tweet_ids   = []
    previous_id = None
    for text in tweets:
        kwargs = {"text": text}
        if previous_id:
            kwargs["in_reply_to_tweet_id"] = previous_id
        resp        = client.create_tweet(**kwargs)
        previous_id = str(resp.data["id"])
        tweet_ids.append(previous_id)

    post_url = f"https://twitter.com/i/web/status/{tweet_ids[0]}"
    _patch_draft(draft_id, status="published",
                 published_at=datetime.now().isoformat(timespec="seconds"),
                 post_id=tweet_ids[0], post_url=post_url,
                 metadata={"tweet_ids": tweet_ids})
    return {"tweet_ids": tweet_ids, "post_url": post_url}


def main() -> None:
    if not SCHEDULE.exists():
        print("store/schedule.json not found. Nothing to publish.")
        return

    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    now      = datetime.now()
    window   = now - timedelta(minutes=65)   # 65 min catches any cron delay

    published = failed = 0

    for entry in schedule.get("schedule", []):
        if entry["status"] != "pending":
            continue
        try:
            due = datetime.fromisoformat(entry["scheduled_for"])
        except ValueError:
            continue
        if not (window <= due <= now):
            continue

        draft_id = entry["draft_id"]
        platform = entry["platform"]
        print(f"Publishing {draft_id} ({platform}) due at {entry['scheduled_for']} ...")

        try:
            if platform == "linkedin":
                result = _publish_linkedin(draft_id)
            elif platform in ("twitter", "twitter_thread"):
                result = _publish_twitter(draft_id)
            else:
                print(f"  Unknown platform '{platform}' — skipping")
                continue

            entry["status"] = "published"
            published += 1
            print(f"  Done: {result.get('post_url', '')}")

        except Exception as e:
            print(f"  FAILED: {e}")
            entry["status"] = "failed"
            failed += 1

    SCHEDULE.write_text(json.dumps(schedule, indent=2), encoding="utf-8")
    print(f"\nRun complete — published: {published}, failed: {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
