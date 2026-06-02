"""
Aggregates analytics from .tmp/analytics/ into a markdown performance report.
Reads all .json files, filters by date range and/or platform, and writes a report.

Usage:
  python tools/generate_report.py [--days 7] [--platform all|linkedin|twitter]

Environment variables: none required

Output:
  - Prints report to stdout
  - Saves to .tmp/report_{date}.md

Report includes:
  - Summary totals per platform
  - Per-post breakdown table
  - Top performer callout
  - Engagement rate benchmarks

Example:
  python tools/generate_report.py --days 30
  python tools/generate_report.py --days 7 --platform linkedin
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

ANALYTICS_DIR = Path(".tmp/analytics")
REPORTS_DIR   = Path(".tmp")

BENCHMARKS = {
    "linkedin": {"good": 0.03, "great": 0.06},
    "twitter":  {"good": 0.01, "great": 0.03},
}


def load_analytics(platform: str | None = None, days: int = 30) -> list[dict]:
    """
    Load all analytics records, optionally filtered.

    Args:
        platform: Filter by 'linkedin' or 'twitter'. None = all.
        days: Only include records fetched within this many days.

    Returns:
        list[dict]: Sorted analytics records (newest first)
    """
    if not ANALYTICS_DIR.exists():
        return []

    cutoff = datetime.now() - timedelta(days=days)
    records = []

    for path in ANALYTICS_DIR.glob("*.json"):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        if platform and platform != "all" and rec.get("platform") != platform:
            continue

        fetched = rec.get("fetched_at", "")
        try:
            if datetime.fromisoformat(fetched) < cutoff:
                continue
        except ValueError:
            pass

        records.append(rec)

    return sorted(records, key=lambda r: r.get("fetched_at", ""), reverse=True)


def _rate_label(rate: float, platform: str) -> str:
    bench = BENCHMARKS.get(platform, {"good": 0.02, "great": 0.05})
    if rate >= bench["great"]:
        return "Excellent"
    if rate >= bench["good"]:
        return "Good"
    return "Below avg"


def generate_report(platform: str | None = None, days: int = 7) -> str:
    """
    Generate a markdown performance report from stored analytics.

    Args:
        platform: Filter platform or None for all
        days: Lookback window in days

    Returns:
        str: Markdown report text
    """
    records = load_analytics(platform=platform, days=days)
    now = datetime.now()
    period_start = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    period_end   = now.strftime("%Y-%m-%d")

    lines = [
        f"# Social Media Performance Report",
        f"",
        f"**Period:** {period_start} to {period_end}  ",
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M')}  ",
        f"**Posts analysed:** {len(records)}",
        f"",
    ]

    if not records:
        lines.append("No analytics data found for this period.")
        report = "\n".join(lines)
        _save_report(report, now)
        return report

    # Summary by platform
    platforms_seen = sorted({r["platform"] for r in records})
    lines += ["## Summary by Platform", ""]

    for p in platforms_seen:
        p_recs = [r for r in records if r["platform"] == p]
        total_imp = sum(r["metrics"].get("impressions", 0) for r in p_recs)
        total_eng = sum(r["metrics"].get("total_engagements", 0) for r in p_recs)
        avg_rate  = round(total_eng / total_imp, 4) if total_imp else 0.0

        lines += [
            f"### {p.capitalize()}",
            f"",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Posts | {len(p_recs)} |",
            f"| Total impressions | {total_imp:,} |",
            f"| Total engagements | {total_eng:,} |",
            f"| Avg engagement rate | {avg_rate:.1%} ({_rate_label(avg_rate, p)}) |",
            f"",
        ]

    # Per-post breakdown
    lines += ["## Post Breakdown", ""]

    for p in platforms_seen:
        p_recs = [r for r in records if r["platform"] == p]
        if not p_recs:
            continue

        lines += [f"### {p.capitalize()}", ""]
        lines += ["| Post ID | Impressions | Engagements | Rate | Rating |"]
        lines += ["|---|---|---|---|---|"]

        for r in p_recs:
            m    = r["metrics"]
            rate = m.get("engagement_rate", 0)
            pid  = r["post_id"]
            # Trim long URNs for readability
            pid_display = pid[-20:] if len(pid) > 20 else pid
            lines.append(
                f"| ...{pid_display} | {m.get('impressions',0):,} | "
                f"{m.get('total_engagements',0):,} | {rate:.1%} | {_rate_label(rate, p)} |"
            )
        lines.append("")

    # Top performer
    if records:
        top = max(records, key=lambda r: r["metrics"].get("engagement_rate", 0))
        m   = top["metrics"]
        lines += [
            "## Top Performer",
            "",
            f"**Platform:** {top['platform'].capitalize()}  ",
            f"**Post ID:** `{top['post_id']}`  ",
            f"**Engagement rate:** {m.get('engagement_rate', 0):.1%}  ",
            f"**Impressions:** {m.get('impressions', 0):,}  ",
            f"**Engagements:** {m.get('total_engagements', 0):,}",
            "",
        ]

    report = "\n".join(lines)
    _save_report(report, now)
    return report


def _save_report(report: str, now: datetime) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"report_{now.strftime('%Y%m%d_%H%M')}.md"
    path = REPORTS_DIR / filename
    path.write_text(report, encoding="utf-8")
    print(f"Report saved -> {path}")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a social media performance report.")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days (default: 7)")
    parser.add_argument("--platform", type=str, default=None,
                        choices=["all", "linkedin", "twitter"],
                        help="Filter by platform (default: all)")
    args = parser.parse_args()

    report = generate_report(platform=args.platform, days=args.days)
    print("\n" + report)
