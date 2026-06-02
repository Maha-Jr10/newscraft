"""
Lists all social media drafts in .tmp/drafts/ with optional filtering.
Displays a formatted summary table and returns the full list.

Usage:
  python tools/list_drafts.py
  python tools/list_drafts.py --platform linkedin
  python tools/list_drafts.py --status draft
  python tools/list_drafts.py --platform twitter --status scheduled

Environment variables: none required

Example output:
  ID         Platform           Status       Chars   Created                Topic
  -----------------------------------------------------------------------------------------
  a3f1b2c4   linkedin           draft        245     2025-06-02T10:30:00    AI trends
  b5e2d1f3   twitter_thread     scheduled    980     2025-06-02T11:00:00    Data Engineering
"""

import sys
import json
import argparse
from pathlib import Path

DRAFTS_DIR = Path(".tmp/drafts")


def list_drafts(platform: str | None = None, status: str | None = None) -> list[dict]:
    """
    Return all drafts, optionally filtered by platform and/or status.
    Results are sorted newest-first by created_at.

    Args:
        platform: Filter by 'linkedin', 'twitter', or 'twitter_thread'. None = all.
        status: Filter by 'draft', 'scheduled', 'published', or 'failed'. None = all.

    Returns:
        list[dict]: Matching draft records sorted by created_at descending
    """
    if not DRAFTS_DIR.exists():
        return []

    drafts = []
    for path in sorted(DRAFTS_DIR.glob("*.json")):
        try:
            draft = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if platform and draft.get("platform") != platform:
            continue
        if status and draft.get("status") != status:
            continue
        drafts.append(draft)

    return sorted(drafts, key=lambda d: d.get("created_at", ""), reverse=True)


def print_table(drafts: list[dict]) -> None:
    """Print a human-readable summary table of drafts."""
    if not drafts:
        print("No drafts found.")
        return

    header = f"{'ID':<10} {'Platform':<20} {'Status':<12} {'Chars':<7} {'Created':<22} {'Topic'}"
    print(f"\n{header}")
    print("-" * 95)
    for d in drafts:
        topic = (d.get("metadata") or {}).get("topic", "")[:32]
        content = d.get("content", "")
        if isinstance(content, list):
            content = content[0] if content else ""
        preview = content[:40].replace("\n", " ")
        print(
            f"{d.get('id',''):<10} "
            f"{d.get('platform',''):<20} "
            f"{d.get('status',''):<12} "
            f"{d.get('char_count', 0):<7} "
            f"{d.get('created_at','')[:19]:<22} "
            f"{topic or preview}"
        )
    print(f"\n{len(drafts)} draft(s) total.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List social media drafts.")
    parser.add_argument("--platform", type=str, default=None,
                        choices=["linkedin", "twitter", "twitter_thread"],
                        help="Filter by platform")
    parser.add_argument("--status", type=str, default=None,
                        choices=["draft", "scheduled", "published", "failed"],
                        help="Filter by status")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="Output raw JSON instead of table")
    args = parser.parse_args()

    drafts = list_drafts(platform=args.platform, status=args.status)
    if args.as_json:
        print(json.dumps(drafts, indent=2))
    else:
        print_table(drafts)
