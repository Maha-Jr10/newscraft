"""
Fetches post performance metrics from LinkedIn or Twitter/X and saves them locally.
Output is saved to .tmp/analytics/{platform}_{post_id}.json for use by generate_report.py.

Usage:
  python tools/fetch_analytics.py --platform linkedin --post-id "urn:li:ugcPost:1234567890"
  python tools/fetch_analytics.py --platform twitter --post-id "1234567890123456789"

Environment variables:
  LinkedIn : LINKEDIN_ACCESS_TOKEN
  Twitter  : TWITTER_BEARER_TOKEN (read-only is sufficient for analytics)
             OR TWITTER_API_KEY + TWITTER_API_SECRET + TWITTER_ACCESS_TOKEN + TWITTER_ACCESS_TOKEN_SECRET

Permissions required:
  LinkedIn : r_organization_social OR r_member_social
  Twitter  : v2 Tweet lookup (public_metrics) — available on Free tier

Metrics collected:
  LinkedIn : impressionCount, likeCount, commentCount, shareCount, engagement_rate
  Twitter  : impression_count, like_count, retweet_count, reply_count, quote_count, engagement_rate

Notes:
  - LinkedIn analytics can take up to 24 hours to populate after posting
  - Twitter impressions require Elevated access or above on v2 API
  - On 401/403: token may have expired or lack required scopes

Example:
  python tools/fetch_analytics.py --platform linkedin --post-id "urn:li:ugcPost:7123456789"
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

ANALYTICS_DIR = Path(".tmp/analytics")


def _safe_post_id(post_id: str) -> str:
    """Sanitise post ID for use as a filename."""
    return post_id.replace(":", "_").replace("/", "_")


def fetch_linkedin_analytics(post_id: str) -> dict:
    """
    Fetch engagement metrics for a LinkedIn UGC post.

    Args:
        post_id: LinkedIn post URN, e.g. urn:li:ugcPost:1234567890

    Returns:
        dict: Normalised analytics record
    """
    access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    if not access_token:
        raise EnvironmentError("LINKEDIN_ACCESS_TOKEN not set in .env")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # Fetch share statistics
    response = requests.get(
        "https://api.linkedin.com/v2/socialMetadata",
        headers=headers,
        params={"q": "urn", "urn": post_id},
    )

    if response.status_code == 404:
        raise ValueError(f"Post not found: {post_id}. It may still be processing (<24h) or the URN is wrong.")
    response.raise_for_status()

    data = response.json()
    social = data.get("socialDetail", data)

    impressions = social.get("impressionCount", 0)
    likes       = social.get("likesSummary", {}).get("totalLikes", 0)
    comments    = social.get("commentsSummary", {}).get("totalFirstLevelComments", 0)
    shares      = social.get("shareCount", 0)
    total_eng   = likes + comments + shares
    eng_rate    = round(total_eng / impressions, 4) if impressions else 0.0

    return {
        "post_id": post_id,
        "platform": "linkedin",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "metrics": {
            "impressions": impressions,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "total_engagements": total_eng,
            "engagement_rate": eng_rate,
        },
    }


def fetch_twitter_analytics(post_id: str) -> dict:
    """
    Fetch public metrics for a Twitter/X tweet.

    Args:
        post_id: Tweet ID as a string

    Returns:
        dict: Normalised analytics record
    """
    try:
        import tweepy
    except ImportError:
        raise ImportError("tweepy is required: pip install tweepy")

    bearer = os.environ.get("TWITTER_BEARER_TOKEN")
    if not bearer:
        # Fall back to user auth
        required = ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"]
        missing = [k for k in required if not os.environ.get(k)]
        if missing:
            raise EnvironmentError(f"Set TWITTER_BEARER_TOKEN or full OAuth credentials in .env. Missing: {', '.join(missing)}")
        client = tweepy.Client(
            consumer_key=os.environ["TWITTER_API_KEY"],
            consumer_secret=os.environ["TWITTER_API_SECRET"],
            access_token=os.environ["TWITTER_ACCESS_TOKEN"],
            access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        )
    else:
        client = tweepy.Client(bearer_token=bearer)

    tweet = client.get_tweet(post_id, tweet_fields=["public_metrics", "created_at"])

    if not tweet.data:
        raise ValueError(f"Tweet {post_id} not found.")

    m = tweet.data.public_metrics or {}
    impressions = m.get("impression_count", 0)
    likes       = m.get("like_count", 0)
    retweets    = m.get("retweet_count", 0)
    replies     = m.get("reply_count", 0)
    quotes      = m.get("quote_count", 0)
    total_eng   = likes + retweets + replies + quotes
    eng_rate    = round(total_eng / impressions, 4) if impressions else 0.0

    return {
        "post_id": post_id,
        "platform": "twitter",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "metrics": {
            "impressions": impressions,
            "likes": likes,
            "retweets": retweets,
            "replies": replies,
            "quotes": quotes,
            "total_engagements": total_eng,
            "engagement_rate": eng_rate,
        },
    }


def fetch_analytics(platform: str, post_id: str) -> dict:
    """
    Fetch analytics for a post and save to .tmp/analytics/.

    Args:
        platform: 'linkedin' or 'twitter'
        post_id: Platform-specific post identifier

    Returns:
        dict: Analytics record saved to disk
    """
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

    if platform == "linkedin":
        record = fetch_linkedin_analytics(post_id)
    elif platform == "twitter":
        record = fetch_twitter_analytics(post_id)
    else:
        raise ValueError(f"Unsupported platform: '{platform}'. Use 'linkedin' or 'twitter'.")

    safe_id   = _safe_post_id(post_id)
    file_name = f"{platform}_{safe_id}.json"
    out_path  = ANALYTICS_DIR / file_name
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    m = record["metrics"]
    print(f"Analytics fetched -> {out_path}")
    print(f"  Impressions : {m.get('impressions', 0):,}")
    print(f"  Engagements : {m.get('total_engagements', 0):,}  (rate: {m.get('engagement_rate', 0):.1%})")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch post analytics from LinkedIn or Twitter.")
    parser.add_argument("--platform", required=True, choices=["linkedin", "twitter"])
    parser.add_argument("--post-id", required=True, help="Platform post ID or URN")
    args = parser.parse_args()
    fetch_analytics(args.platform, args.post_id)
