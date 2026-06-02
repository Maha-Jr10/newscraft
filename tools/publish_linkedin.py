"""
Publishes a social media draft to LinkedIn via the UGC Posts API.
Loads the draft from .tmp/drafts/{draft_id}.json, posts it, and updates the draft record.

Usage:
  python tools/publish_linkedin.py --draft-id <id>
  python tools/publish_linkedin.py --draft-id <id> --dry-run

Environment variables (required):
  LINKEDIN_ACCESS_TOKEN  : OAuth 2.0 bearer token (scope: w_member_social)
  LINKEDIN_PERSON_URN    : Your person URN, e.g. urn:li:person:AbCdEfGhIj
                           Get from: GET https://api.linkedin.com/v2/userinfo

Output:
  - Prints the LinkedIn post URL
  - Updates draft: status=published, post_id, post_url, published_at

Getting credentials:
  1. Go to https://developer.linkedin.com and create an app
  2. Request 'Sign In with LinkedIn using OpenID Connect' and 'Share on LinkedIn' products
  3. Generate an OAuth 2.0 token with scope w_member_social
  4. Fetch your person URN: GET https://api.linkedin.com/v2/userinfo (field: sub)

Rate limits:
  - 150 requests/day per user token for ugcPosts
  - Do not retry on 429; wait 24 hours

Example:
  python tools/publish_linkedin.py --draft-id a3f1b2c4
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
DRAFTS_DIR = Path(".tmp/drafts")


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


def _build_post_text(draft: dict) -> str:
    """Combine content and hashtags into the final post text."""
    content = draft.get("content", "")
    if isinstance(content, list):
        content = "\n\n".join(content)
    hashtags = draft.get("hashtags", [])
    if hashtags:
        tag_str = " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)
        content = f"{content}\n\n{tag_str}"
    return content


def publish_linkedin(draft_id: str, dry_run: bool = False) -> dict:
    """
    Post a draft to LinkedIn.

    Args:
        draft_id: ID of the draft to publish from .tmp/drafts/
        dry_run: If True, build the payload and print it without posting

    Returns:
        dict: Result with post_id and post_url

    Raises:
        FileNotFoundError: Draft not found
        EnvironmentError: Missing API credentials
        requests.HTTPError: LinkedIn API error
    """
    access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    person_urn   = os.environ.get("LINKEDIN_PERSON_URN")

    if not access_token:
        raise EnvironmentError("LINKEDIN_ACCESS_TOKEN not set in .env")
    if not person_urn:
        raise EnvironmentError("LINKEDIN_PERSON_URN not set in .env (e.g. urn:li:person:AbCdEfGhIj)")

    draft = _load_draft(draft_id)

    if draft["platform"] not in ("linkedin",):
        raise ValueError(f"Draft platform is '{draft['platform']}', expected 'linkedin'")

    post_text = _build_post_text(draft)

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    if dry_run:
        print("[DRY RUN] Would POST to LinkedIn UGC Posts API:")
        print(json.dumps(payload, indent=2))
        return {"dry_run": True, "payload": payload}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    response = requests.post(f"{LINKEDIN_API_BASE}/ugcPosts", headers=headers, json=payload)

    if response.status_code not in (200, 201):
        print(f"LinkedIn API error {response.status_code}: {response.text}")
        _patch_draft(draft_id, status="failed")
        response.raise_for_status()

    # Extract post ID from response header or body
    post_id = response.headers.get("x-restli-id") or response.json().get("id", "")
    post_url = f"https://www.linkedin.com/feed/update/{post_id}/" if post_id else ""

    _patch_draft(
        draft_id,
        status="published",
        published_at=datetime.now().isoformat(timespec="seconds"),
        post_id=post_id,
        post_url=post_url,
    )

    print(f"Published to LinkedIn!")
    print(f"  Post ID  : {post_id}")
    print(f"  Post URL : {post_url}")
    return {"post_id": post_id, "post_url": post_url}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish a draft to LinkedIn.")
    parser.add_argument("--draft-id", required=True, help="Draft ID from .tmp/drafts/")
    parser.add_argument("--dry-run", action="store_true", help="Print payload without posting")
    args = parser.parse_args()
    publish_linkedin(args.draft_id, dry_run=args.dry_run)
