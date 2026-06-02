# Workflow: Social Media Analytics & Performance Reporting

## Objective
Fetch post-level engagement metrics from LinkedIn and Twitter, aggregate them into a performance report, and identify top-performing content.

## How the Work is Divided

| Layer | Who does it | What they do |
|---|---|---|
| Data collection | `tools/fetch_analytics.py` | Pull metrics from platform APIs |
| Aggregation | `tools/generate_report.py` | Summarise analytics into a report |
| Interpretation | Agent | Read the report and surface insights |

## Required Inputs

| Input | Description | Default |
|---|---|---|
| `post_ids` | List of post IDs to fetch | All published drafts |
| `platforms` | Which platforms to report on | `all` |
| `days` | Lookback window for report | `7` |

## Outputs
- `.tmp/analytics/{platform}_{post_id}.json` per post
- `.tmp/report_{datetime}.md` — performance report

## Execution Steps

### Step 1 — Identify published posts
```
python tools/list_drafts.py --status published
```
Collect the `post_id` and `platform` for each published post you want to analyse.

### Step 2 — Fetch analytics per post
Run for each post:

**LinkedIn:**
```
python tools/fetch_analytics.py --platform linkedin --post-id "urn:li:ugcPost:XXXXXXXXXX"
```

**Twitter:**
```
python tools/fetch_analytics.py --platform twitter --post-id "1234567890123456789"
```

Timing:
- LinkedIn: run 24+ hours after posting (metrics take time to populate)
- Twitter: run 1-48 hours after posting for stable numbers

Repeat for all posts.

### Step 3 — Generate report
```
python tools/generate_report.py --days 7
```

Optional filters:
```
python tools/generate_report.py --days 30 --platform linkedin
```

Output: `.tmp/report_{datetime}.md`

### Step 4 — Interpret results (agent does this)
Read the report and summarise:
1. **Top performer** — which post got the highest engagement rate and why
2. **Platform comparison** — which platform is outperforming and by how much
3. **Content pattern** — what topic/format/angle performed best
4. **Recommendation** — one specific change to make for next week's content

Present the interpretation to the user in 3-5 bullet points.

---

## Validation Checks
- [ ] All analytics files are newer than the post's `published_at` timestamp
- [ ] Report covers the expected date range
- [ ] At least one record exists in `.tmp/analytics/` before running generate_report.py
- [ ] Engagement rate is between 0% and 100% (flag anomalies)

## Error Handling
- **LinkedIn 404** → Post may not have propagated yet (< 1 hour). Wait and retry.
- **Twitter 401** → Bearer token invalid or expired. Regenerate at developer.twitter.com.
- **Empty analytics** → All published posts are < 1h old. Schedule analytics collection for later.
- **Analytics file already exists** → `fetch_analytics.py` overwrites it with fresh data — this is intentional.
- **generate_report.py finds no files** → `.tmp/analytics/` is empty. Run `fetch_analytics.py` first.

## Benchmarks

| Platform | Good engagement rate | Great engagement rate |
|---|---|---|
| LinkedIn | 3%+ | 6%+ |
| Twitter  | 1%+ | 3%+ |

These are built into `generate_report.py` as the `BENCHMARKS` constant.

## Lessons Learned
- LinkedIn impressions are often 5-10x raw follower count if the post gets early engagement — the first 30 minutes matter most
- Twitter impression data requires Elevated API access; Free tier only returns like/retweet/reply counts
- Always fetch analytics after 48 hours, not just after 24 — LinkedIn numbers often keep climbing for 3-5 days
- Threads show analytics on the first tweet only; to get aggregate thread performance you must fetch each tweet individually
- Consistency of posting beats viral outliers — track 30-day trends, not individual posts
