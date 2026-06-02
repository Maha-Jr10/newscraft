"""
Publishes a social media draft to Twitter/X via the v2 API using Tweepy.
Supports single tweets (platform: twitter) and threads (platform: twitter_thread).
Loads draft from .tmp/drafts/{draft_id}.json, posts it, and updates the draft record.

Usage:
  python tools/publish_twitter.py --draft-id <id>
  python tools/publish_twitter.py --draft-id <id> --dry-run

Environment variables (required):
  TWITTER_API_KEY             : API key (consumer key)
  TWITTER_API_SECRET          : API key secret (consumer secret)
  TWITTER_ACCESS_TOKEN        : Access token
  TWITTER_ACCESS_TOKEN_SECRET : Access token secret

Getting credentials:
  1. Go to https://developer.twitter.com and create a project + app
  2. Set app permissions to 'Read and Write'
  3. Generate access token and secret under 'Keys and Tokens'
  4. Minimum required plan: Free tier (1,500 tweets/month write limit)

Rate limits:
  - Free tier: 1,500 tweets/month
  - Basic tier: 3,000 tweets/month, 300/15min
  - On 429: back off for 15 minutes before retrying

Thread behavior:
  - Each tweet in the list is posted as a reply to the previous one
  - The first tweet starts the thread; subsequent tweets reply to it
  - Each tweet must be <= 280 characters (validation enforced here)

Example:
  python tools/publish_twitter.py --draft-id b5e2d1f3
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DRAFTS_DIR = Path(".tmp/drafts")
TWITTER_URL = "https://twitter.com/i/web/status/{tweet_id}"


def _load_draft(draft_id: str) -> dict:
    path = DRAFTS_DIR / f"{draft_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Draft '{draft_id}' not found.")
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_draft(draft_id: str, **updates) -> None:
    path = DRAFTS_DIR / f"{draft_id}.json"
    draft = json.loads(path.read_text(encoding="utf-8"))
    draft.update(updates)
    draft["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path.write_text(json.dumps(draft, indent=2), encoding="utf-8")


def _get_client():
    """Build and return an authenticated Tweepy v2 client."""
    try:
        import tweepy
    except ImportError:
        raise ImportError("tweepy is required: pip install tweepy")

    required = ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(f"Missing Twitter credentials in .env: {', '.join(missing)}")

    return tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,
    )


def _validate_tweets(tweets: list[str]) -> list[str]:
    """Validate tweet lengths and raise if any exceed 280 chars."""
    errors = []
    for i, tweet in enumerate(tweets, 1):
        if len(tweet) > 280:
            errors.append(f"Tweet {i} is {len(tweet)} chars (max 280): '{tweet[:60]}...'")
    if errors:
        raise ValueError("Tweet length violations:\n" + "\n".join(errors))
    return tweets


def publish_twitter(draft_id: str, dry_run: bool = False) -> dict:
    """
    Publish a single tweet or a thread to Twitter/X.

    Args:
        draft_id: ID of the draft in .tmp/drafts/
        dry_run: If True, validate and print tweets without posting

    Returns:
        dict: Result with tweet_ids and post_url

    Raises:
        FileNotFoundError: Draft not found
        EnvironmentError: Missing credentials
        ValueError: Tweet content too long or wrong platform
        tweepy.errors.TweepyException: Twitter API error
    """
    draft = _load_draft(draft_id)
    platform = draft["platform"]

    if platform not in ("twitter", "twitter_thread"):
        raise ValueError(f"Draft platform is '{platform}', expected 'twitter' or 'twitter_thread'")

    # Normalise content to list
    content = draft.get("content", "")
    tweets = content if isinstance(content, list) else [content]

    # Append hashtags to last tweet if present
    hashtags = draft.get("hashtags", [])
    if hashtags:
        tag_str = " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)
        last = tweets[-1]
        if len(last) + 1 + len(tag_str) <= 280:
            tweets = tweets[:-1] + [f"{last}\n\n{tag_str}"]

    _validate_tweets(tweets)

    if dry_run:
        print(f"[DRY RUN] Would publish {len(tweets)} tweet(s):")
        for i, t in enumerate(tweets, 1):
            print(f"\n--- Tweet {i} ({len(t)} chars) ---\n{t}")
        return {"dry_run": True, "tweet_count": len(tweets)}

    client = _get_client()
    tweet_ids = []
    previous_id = None

    for i, text in enumerate(tweets, 1):
        kwargs = {"text": text}
        if previous_id:
            kwargs["in_reply_to_tweet_id"] = previous_id

        response = client.create_tweet(**kwargs)
        tweet_id = str(response.data["id"])
        tweet_ids.append(tweet_id)
        previous_id = tweet_id
        print(f"  Posted tweet {i}/{len(tweets)}: {tweet_id}")

    first_id = tweet_ids[0]
    post_url = TWITTER_URL.format(tweet_id=first_id)

    _patch_draft(
        draft_id,
        status="published",
        published_at=datetime.now().isoformat(timespec="seconds"),
        post_id=first_id,
        post_url=post_url,
        metadata={"tweet_ids": tweet_ids},
    )

    print(f"\nPublished {len(tweet_ids)} tweet(s) to X/Twitter!")
    print(f"  First tweet : {post_url}")
    return {"tweet_ids": tweet_ids, "post_url": post_url}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish a draft to Twitter/X.")
    parser.add_argument("--draft-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    publish_twitter(args.draft_id, dry_run=args.dry_run)
