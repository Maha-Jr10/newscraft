"""
Creates and manages a content calendar for social media planning.
Calendar files are stored as .tmp/calendar_{year}_{week}.json.

Usage:
  python tools/manage_calendar.py create --week 2025-W23 [--linkedin 3] [--twitter 5]
  python tools/manage_calendar.py view   --week 2025-W23
  python tools/manage_calendar.py update --week 2025-W23 --slot 2 --topic "AI in healthcare" --draft-id abc123

Environment variables: none required

Calendar slot schema:
  date        : YYYY-MM-DD
  day         : Monday, Tuesday, etc.
  time        : Suggested posting time (e.g. 09:00)
  platform    : linkedin | twitter | twitter_thread
  topic       : Content topic (filled by agent)
  draft_id    : Linked draft ID once content is created
  status      : empty | planned | drafted | scheduled | published

Optimal posting times used by default:
  LinkedIn : Tue/Wed/Thu 08:00-10:00
  Twitter  : Mon-Fri 09:00, 12:00, 17:00

Example:
  python tools/manage_calendar.py create --week 2025-W23 --linkedin 3 --twitter 5
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

CALENDAR_DIR = Path(".tmp")

# Suggested posting times by platform and day (0=Mon ... 6=Sun)
OPTIMAL_TIMES = {
    "linkedin": {0: "09:00", 1: "08:30", 2: "09:00", 3: "08:30", 4: "10:00"},
    "twitter":  {0: "09:00", 1: "09:00", 2: "12:00", 3: "09:00", 4: "17:00", 5: "12:00", 6: "12:00"},
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _week_dates(week_str: str) -> list[datetime]:
    """Return the 7 dates for a given ISO week string (e.g. '2025-W23')."""
    year, week = week_str.split("-W")
    monday = datetime.strptime(f"{year}-W{int(week):02d}-1", "%Y-W%W-%w")
    return [monday + timedelta(days=i) for i in range(7)]


def _calendar_path(week_str: str) -> Path:
    safe = week_str.replace("-", "_")
    return CALENDAR_DIR / f"calendar_{safe}.json"


def create_calendar(week_str: str, linkedin_slots: int = 3, twitter_slots: int = 5) -> dict:
    """
    Generate a new content calendar for the specified ISO week.

    Args:
        week_str: ISO week string e.g. '2025-W23'
        linkedin_slots: Number of LinkedIn posts to plan
        twitter_slots: Number of Twitter posts to plan

    Returns:
        dict: The calendar structure saved to disk
    """
    dates   = _week_dates(week_str)
    slots   = []
    li_used = 0
    tw_used = 0

    # Distribute LinkedIn slots: prefer Tue, Wed, Thu
    li_days = [1, 2, 3, 0, 4]  # preferred day order
    for weekday in li_days:
        if li_used >= linkedin_slots:
            break
        if weekday >= len(dates):
            continue
        d = dates[weekday]
        slots.append({
            "date": d.strftime("%Y-%m-%d"),
            "day": DAYS[weekday],
            "time": OPTIMAL_TIMES["linkedin"].get(weekday, "09:00"),
            "platform": "linkedin",
            "topic": "",
            "draft_id": None,
            "status": "empty",
        })
        li_used += 1

    # Distribute Twitter slots across the week
    tw_days = [0, 1, 2, 3, 4, 5, 6]
    tw_per_day = max(1, -(-twitter_slots // len(tw_days)))  # ceiling division
    for weekday in tw_days:
        if tw_used >= twitter_slots:
            break
        if weekday >= len(dates):
            continue
        d = dates[weekday]
        slots.append({
            "date": d.strftime("%Y-%m-%d"),
            "day": DAYS[weekday],
            "time": OPTIMAL_TIMES["twitter"].get(weekday, "09:00"),
            "platform": "twitter",
            "topic": "",
            "draft_id": None,
            "status": "empty",
        })
        tw_used += 1

    # Sort by date then time
    slots.sort(key=lambda s: (s["date"], s["time"]))

    calendar = {
        "week": week_str,
        "start_date": dates[0].strftime("%Y-%m-%d"),
        "end_date": dates[6].strftime("%Y-%m-%d"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "slots": slots,
    }

    path = _calendar_path(week_str)
    CALENDAR_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(calendar, indent=2), encoding="utf-8")
    print(f"Calendar created -> {path}")
    print(f"  Week    : {week_str} ({calendar['start_date']} to {calendar['end_date']})")
    print(f"  LinkedIn: {li_used} slot(s)")
    print(f"  Twitter : {tw_used} slot(s)")
    return calendar


def view_calendar(week_str: str) -> None:
    """Print a formatted view of the calendar for the given week."""
    path = _calendar_path(week_str)
    if not path.exists():
        print(f"No calendar found for {week_str}. Run: python tools/manage_calendar.py create --week {week_str}")
        return

    cal = json.loads(path.read_text(encoding="utf-8"))
    print(f"\nContent Calendar: {week_str} ({cal['start_date']} to {cal['end_date']})")
    print(f"\n{'#':<4} {'Date':<12} {'Day':<12} {'Time':<7} {'Platform':<20} {'Status':<12} {'Topic / Draft'}")
    print("-" * 100)
    for i, s in enumerate(cal["slots"]):
        detail = s.get("topic", "") or (f"[draft: {s['draft_id']}]" if s.get("draft_id") else "-")
        print(
            f"{i:<4} {s['date']:<12} {s['day']:<12} {s['time']:<7} "
            f"{s['platform']:<20} {s['status']:<12} {detail[:35]}"
        )
    print(f"\n{len(cal['slots'])} slot(s) total.\n")


def update_slot(week_str: str, slot_index: int, topic: str | None = None, draft_id: str | None = None, status: str | None = None) -> dict:
    """
    Update a specific slot in the calendar.

    Args:
        week_str: ISO week string
        slot_index: Zero-based index of the slot to update
        topic: Content topic to assign
        draft_id: Link to an existing draft ID
        status: New status for the slot

    Returns:
        dict: Updated calendar
    """
    path = _calendar_path(week_str)
    if not path.exists():
        raise FileNotFoundError(f"Calendar for {week_str} not found.")

    cal = json.loads(path.read_text(encoding="utf-8"))

    if slot_index < 0 or slot_index >= len(cal["slots"]):
        raise IndexError(f"Slot index {slot_index} out of range (0-{len(cal['slots'])-1}).")

    slot = cal["slots"][slot_index]
    if topic:
        slot["topic"]    = topic
        slot["status"]   = status or ("planned" if slot["status"] == "empty" else slot["status"])
    if draft_id:
        slot["draft_id"] = draft_id
        slot["status"]   = status or "drafted"
    if status:
        slot["status"]   = status

    path.write_text(json.dumps(cal, indent=2), encoding="utf-8")
    print(f"Slot {slot_index} updated: {slot['date']} {slot['platform']} -> topic='{slot.get('topic','')}' status={slot['status']}")
    return cal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage the content calendar.")
    sub = parser.add_subparsers(dest="action")

    p_create = sub.add_parser("create", help="Create a new calendar for a week")
    p_create.add_argument("--week", required=True, help="ISO week e.g. 2025-W23")
    p_create.add_argument("--linkedin", type=int, default=3)
    p_create.add_argument("--twitter",  type=int, default=5)

    p_view = sub.add_parser("view", help="View a week's calendar")
    p_view.add_argument("--week", required=True)

    p_update = sub.add_parser("update", help="Update a calendar slot")
    p_update.add_argument("--week",     required=True)
    p_update.add_argument("--slot",     type=int, required=True)
    p_update.add_argument("--topic",    type=str, default=None)
    p_update.add_argument("--draft-id", type=str, default=None)
    p_update.add_argument("--status",   type=str, default=None)

    args = parser.parse_args()

    if args.action == "create":
        create_calendar(args.week, linkedin_slots=args.linkedin, twitter_slots=args.twitter)
    elif args.action == "view":
        view_calendar(args.week)
    elif args.action == "update":
        update_slot(args.week, args.slot, topic=args.topic, draft_id=getattr(args, "draft_id", None), status=args.status)
    else:
        parser.print_help()
