"""
Moves a draft from .tmp/drafts/ to store/drafts/ and adds it to store/schedule.json
so GitHub Actions can auto-publish it on schedule.

Usage:
  python tools/push_to_store.py <draft_id> <publish_at>
  publish_at: ISO datetime e.g. 2025-06-10T09:00:00

What this does:
  1. Copies .tmp/drafts/{draft_id}.json -> store/drafts/{draft_id}.json
  2. Adds an entry to store/schedule.json
  3. You then commit and push — GitHub Actions does the rest

Environment variables: none required

Example:
  python tools/push_to_store.py a3f1b2c4 2025-06-10T09:00:00
"""

import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

TMP_DRAFTS   = Path(".tmp/drafts")
STORE_DRAFTS = Path("store/drafts")
SCHEDULE     = Path("store/schedule.json")


def push_to_store(draft_id: str, publish_at: str) -> dict:
    """
    Copy draft to store/ and add to the auto-publish schedule.

    Args:
        draft_id: Existing draft ID in .tmp/drafts/
        publish_at: ISO datetime string for publish time

    Returns:
        dict: The schedule entry created
    """
    # Validate draft exists
    src = TMP_DRAFTS / f"{draft_id}.json"
    if not src.exists():
        raise FileNotFoundError(f"Draft '{draft_id}' not found in {TMP_DRAFTS}")

    # Validate datetime
    try:
        dt = datetime.fromisoformat(publish_at)
    except ValueError:
        raise ValueError(f"Invalid datetime '{publish_at}'. Use YYYY-MM-DDTHH:MM:SS")

    if dt <= datetime.now():
        raise ValueError(f"Scheduled time must be in the future.")

    # Copy draft to store
    STORE_DRAFTS.mkdir(parents=True, exist_ok=True)
    dst = STORE_DRAFTS / f"{draft_id}.json"
    shutil.copy2(src, dst)

    # Load draft to get platform
    draft = json.loads(dst.read_text(encoding="utf-8"))

    # Add to store schedule
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8")) if SCHEDULE.exists() else {"schedule": []}
    schedule["schedule"] = [e for e in schedule["schedule"] if e.get("draft_id") != draft_id]
    entry = {
        "draft_id": draft_id,
        "platform": draft["platform"],
        "scheduled_for": publish_at,
        "status": "pending",
        "added_at": datetime.now().isoformat(timespec="seconds"),
    }
    schedule["schedule"].append(entry)
    schedule["schedule"].sort(key=lambda e: e["scheduled_for"])
    SCHEDULE.write_text(json.dumps(schedule, indent=2), encoding="utf-8")

    print(f"Pushed to store:")
    print(f"  Draft  : store/drafts/{draft_id}.json")
    print(f"  Publish: {publish_at} ({draft['platform']})")
    print(f"\nNext step: commit and push to GitHub")
    print(f"  git add store/")
    print(f"  git commit -m 'schedule: {draft['platform']} post for {publish_at}'")
    print(f"  git push")
    return entry


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/push_to_store.py <draft_id> <publish_at>")
        print("Example: python tools/push_to_store.py a3f1b2c4 2025-06-10T09:00:00")
        sys.exit(1)
    push_to_store(sys.argv[1], sys.argv[2])
