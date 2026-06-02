"""
Saves or updates a social media post draft to .tmp/drafts/{id}.json.
Supports platforms: linkedin, twitter, twitter_thread

Usage:
  python tools/save_draft.py --platform linkedin --content "Your post text" [--hashtags "#AI" "#Data"] [--topic "AI trends"] [--id existing_draft_id]

Environment variables: none required

Draft schema:
  id            : 8-char hex ID (auto-generated on first save)
  platform      : linkedin | twitter | twitter_thread
  status        : draft | scheduled | published | failed
  content       : str (single post) or list[str] (thread tweets)
  hashtags      : list of hashtag strings
  metadata      : dict — topic, tone, source, etc.
  char_count    : total character count
  created_at    : ISO datetime
  updated_at    : ISO datetime
  scheduled_for : ISO datetime | null
  published_at  : ISO datetime | null
  post_id       : platform-assigned ID after publishing | null
  post_url      : public post URL after publishing | null

Example:
  python tools/save_draft.py --platform linkedin --content "AI is reshaping data engineering..." --hashtags "#AI" "#DataEngineering" --topic "AI impact"
"""

import sys
import json
import secrets
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

DRAFTS_DIR = Path(".tmp/drafts")


def save_draft(
    platform: str,
    content: str | list[str],
    hashtags: list[str] | None = None,
    metadata: dict | None = None,
    draft_id: str | None = None,
    status: str = "draft",
    scheduled_for: str | None = None,
    published_at: str | None = None,
    post_id: str | None = None,
    post_url: str | None = None,
) -> dict:
    """
    Save a new draft or update an existing one (by draft_id).
    Returns the saved draft dict with its assigned ID.

    Args:
        platform: Target platform — 'linkedin', 'twitter', or 'twitter_thread'
        content: Post text (str) or list of tweet strings for threads
        hashtags: Optional list of hashtag strings e.g. ['#AI', '#Data']
        metadata: Optional context dict (topic, tone, source newsletter, etc.)
        draft_id: If provided, update the existing draft with this ID
        status: One of 'draft', 'scheduled', 'published', 'failed'
        scheduled_for: ISO datetime string for scheduled publishing
        published_at: ISO datetime string set after publishing
        post_id: Platform post ID set after publishing
        post_url: Public post URL set after publishing

    Returns:
        dict: The full draft record as saved to disk
    """
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")

    # Load existing draft if updating
    existing = None
    if draft_id:
        path = DRAFTS_DIR / f"{draft_id}.json"
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))

    if existing:
        draft = existing
        draft["updated_at"] = now
        if platform:
            draft["platform"] = platform
        if content is not None:
            draft["content"] = content
        if hashtags is not None:
            draft["hashtags"] = hashtags
        if metadata:
            draft["metadata"].update(metadata)
        if status and status != "draft":
            draft["status"] = status
        if scheduled_for is not None:
            draft["scheduled_for"] = scheduled_for
        if published_at is not None:
            draft["published_at"] = published_at
        if post_id is not None:
            draft["post_id"] = post_id
        if post_url is not None:
            draft["post_url"] = post_url
    else:
        assigned_id = draft_id or secrets.token_hex(4)
        draft = {
            "id": assigned_id,
            "platform": platform,
            "status": status,
            "content": content,
            "hashtags": hashtags or [],
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
            "scheduled_for": scheduled_for,
            "published_at": published_at,
            "post_id": post_id,
            "post_url": post_url,
        }

    # Compute char count
    c = draft["content"]
    draft["char_count"] = sum(len(t) for t in c) if isinstance(c, list) else len(c)

    path = DRAFTS_DIR / f"{draft['id']}.json"
    path.write_text(json.dumps(draft, indent=2), encoding="utf-8")
    print(f"Draft saved -> {path}  [id: {draft['id']}, platform: {draft['platform']}, status: {draft['status']}]")
    return draft


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save a social media draft.")
    parser.add_argument("--platform", required=True, choices=["linkedin", "twitter", "twitter_thread"])
    parser.add_argument("--content", type=str, required=True)
    parser.add_argument("--hashtags", nargs="*", default=[])
    parser.add_argument("--topic", type=str, default="")
    parser.add_argument("--tone", type=str, default="professional")
    parser.add_argument("--id", dest="draft_id", type=str, default=None)
    args = parser.parse_args()

    draft = save_draft(
        platform=args.platform,
        content=args.content,
        hashtags=args.hashtags,
        metadata={"topic": args.topic, "tone": args.tone},
        draft_id=args.draft_id,
    )
    print(json.dumps(draft, indent=2))
