# Workflow: Publish Content to Social Media

## Objective
Publish an approved draft to its target platform, update the draft record, and initiate analytics collection.

## How the Work is Divided

| Layer | Who does it | What they do |
|---|---|---|
| Pre-flight check | Agent | Verify draft, platform, credentials |
| Publishing | `tools/publish_linkedin.py` OR `tools/publish_twitter.py` | Deterministic API call |
| Post-publish | `tools/fetch_analytics.py` | Collect initial metrics |

**⚠️ This workflow requires explicit user approval before executing the publish step.**

## Required Inputs

| Input | Description | Default |
|---|---|---|
| `draft_id` | ID of draft to publish | — (required) |
| `dry_run` | Validate without posting | `false` |

## Outputs
- Draft status updated to `"published"` with `post_id` and `post_url`
- Analytics record created in `.tmp/analytics/` (after a delay — see Step 3)

## Execution Steps

### Step 1 — Pre-flight check

Review the draft:
```
python tools/list_drafts.py --status draft
```

Verify:
1. Draft exists and status = "draft" or "scheduled"
2. Platform matches the intended target
3. Required credentials are set in `.env`:
   - LinkedIn: `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`
   - Twitter: `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET`

Show the user the full post content and ask:
> "Publishing to **{platform}** as **{person_urn or @handle}**:
>
> {post content}
>
> Confirm publish? This cannot be undone."

**Stop here until user confirms.**

### Step 2 — Dry run (recommended on first use)
```
python tools/publish_linkedin.py --draft-id <id> --dry-run
# or
python tools/publish_twitter.py --draft-id <id> --dry-run
```
Prints the exact payload that will be sent without posting.

### Step 3 — Publish

**LinkedIn:**
```
python tools/publish_linkedin.py --draft-id <draft_id>
```

**Twitter (single tweet or thread):**
```
python tools/publish_twitter.py --draft-id <draft_id>
```

On success:
- Post ID and URL are printed
- Draft is updated: `status=published`, `post_id`, `post_url`, `published_at`

### Step 4 — Collect analytics (wait 1-24 hours)
LinkedIn analytics take up to 24 hours to populate. Twitter metrics are near real-time.

After the appropriate delay, run:
```
python tools/fetch_analytics.py --platform <platform> --post-id <post_id>
```

For Twitter: run 1-2 hours after posting.
For LinkedIn: run the following morning.

---

## Validation Checks
- [ ] Explicit user confirmation received before Step 3
- [ ] Dry run executed on first publish to a new platform
- [ ] Draft status confirmed as "draft" or "scheduled" before publishing
- [ ] Post URL logged and accessible after publish
- [ ] Draft record shows `published_at` timestamp after success

## Error Handling
- **401 Unauthorized** → Token expired. Regenerate in LinkedIn Developer Portal or Twitter Developer Portal.
- **403 Forbidden** → Insufficient API scopes. LinkedIn needs `w_member_social`; Twitter needs "Read and Write" permissions.
- **429 Rate Limited** → Do not retry immediately. LinkedIn: wait 24h. Twitter Free tier: 1,500 tweets/month — check usage.
- **Publish fails partway through a thread** → `publish_twitter.py` logs each tweet ID as it goes. Manually note where it stopped and resume from that tweet — do not re-post already-published tweets.
- **Draft already published** → `save_draft.py` status = "published". Do not re-publish; create a new draft instead.

## Lessons Learned
- Always do a dry run when publishing to a new platform or after a token refresh
- LinkedIn `X-Restli-Id` header contains the post URN — `publish_linkedin.py` reads it from headers first, then falls back to response body
- Twitter threads that fail midway still leave the published tweets live — check the thread manually before deciding whether to delete and retry
- Do not publish more than 3 LinkedIn posts per day — the algorithm suppresses the second and third
- After publishing, log the post URL somewhere persistent (Google Sheets, Notion) as `.tmp/` is ephemeral
