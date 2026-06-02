"""
Adds a draft to the content schedule (.tmp/schedule.json) and marks it 'scheduled'.

Usage:
  python tools/schedule_post.py <draft_id> <publish_at>
  publish_at: ISO datetime string, e.g. 2025-06-10T09:00:00

Environment variables: none required

Output:
  - Updates .tmp/schedule.json with the new scheduled entry
  - Patches the draft file status to 'scheduled'
  - Prints confirmation with scheduled time

Example:
  python tools/schedule_post.py a3f1b2c4 2025-06-10T09:00:00
"""

import sys
import json
from datetime import datetime
from pathlib import Path

DRAFTS_DIR    = Path(".tmp/drafts")
SCHEDULE_FILE = Path(".tmp/schedule.json")


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


def _load_schedule() -> dict:
    if SCHEDULE_FILE.exists():
        return json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    return {"schedule": []}


def schedule_post(draft_id: str, publish_at: str) -> dict:
    """
    Schedule a draft for publishing at a specific datetime.

    Args:
        draft_id: ID of an existing draft in .tmp/drafts/
        publish_at: ISO datetime string for the desired publish time

    Returns:
        dict: The schedule entry that was created

    Raises:
        FileNotFoundError: If draft does not exist
        ValueError: If publish_at is not a valid ISO datetime or is in the past
    """
    draft = _load_draft(draft_id)

    try:
        scheduled_dt = datetime.fromisoformat(publish_at)
    except ValueError:
        raise ValueError(f"Invalid datetime '{publish_at}'. Use format YYYY-MM-DDTHH:MM:SS")

    if scheduled_dt <= datetime.now():
        raise ValueError(f"Scheduled time {publish_at} must be in the future.")

    schedule = _load_schedule()

    # Remove any existing schedule entry for this draft (reschedule case)
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

    SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_FILE.write_text(json.dumps(schedule, indent=2), encoding="utf-8")

    _patch_draft(draft_id, status="scheduled", scheduled_for=publish_at)

    print(f"Scheduled: draft={draft_id} platform={draft['platform']} at={publish_at}")
    print(f"Schedule file -> {SCHEDULE_FILE}")
    return entry


def view_schedule() -> None:
    """Print the current content schedule."""
    schedule = _load_schedule()
    entries = schedule.get("schedule", [])
    if not entries:
        print("Schedule is empty.")
        return

    print(f"\n{'Draft ID':<12} {'Platform':<20} {'Scheduled For':<22} {'Status'}")
    print("-" * 75)
    for e in entries:
        print(f"{e['draft_id']:<12} {e['platform']:<20} {e['scheduled_for']:<22} {e['status']}")
    print(f"\n{len(entries)} item(s) in schedule.\n")


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "view":
        view_schedule()
    elif len(sys.argv) >= 3:
        schedule_post(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python tools/schedule_post.py <draft_id> <publish_at>")
        print("       python tools/schedule_post.py view")
        sys.exit(1)
