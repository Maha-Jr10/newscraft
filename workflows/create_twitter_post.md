# Workflow: Create Twitter/X Post

## Objective
Write a single punchy tweet on a given topic and save it as a draft for review.

## How the Work is Divided

| Layer | Who does it | What they do |
|---|---|---|
| Research (optional) | `tools/research_topic.py` | Fetch a key stat or fact to anchor the tweet |
| Writing | Claude (the agent) | Write the tweet — brevity is a craft skill |
| Saving | `tools/save_draft.py` | Persist the draft |

## Required Inputs

| Input | Description | Default |
|---|---|---|
| `topic` | What the tweet is about | — (required) |
| `angle` | Hook style | `"insight"` — see angle types below |
| `hashtags` | Tags to append | 0-2 tags (more hurts reach) |
| `cta` | Whether to include a call-to-action | `false` |

**Angle types:**
- `insight` — Share a non-obvious observation
- `stat` — Lead with a surprising number
- `question` — Ask something the audience is already thinking
- `hot-take` — Contrarian but defensible opinion
- `thread-hook` — Designed to pull people into a thread

## Outputs
- `.tmp/drafts/{id}.json` — saved Twitter draft

## Execution Steps

### Step 1 — Research (optional, 1-3 results only)
```
python tools/research_topic.py "<topic>" 3
```
Use only if a specific fact, stat, or current event is needed to make the tweet credible.

### Step 2 — Write the tweet (agent does this)

**Format rules:**
- **Max 280 characters** — hard limit enforced by `publish_twitter.py`
- Single clear point — one idea per tweet
- No thread indicators (1/, 2/) in single tweets
- Hashtags go at the end, never mid-sentence
- Avoid "RT if you agree" — Twitter's algorithm penalises it

**Character budget planning:**
- Hook/insight: ~200-220 characters
- Hashtags (if any): 2 tags × ~15 chars = ~30 characters
- Buffer: ~30 characters for edits
- Target: 220-260 characters

**Draft the tweet, then count characters before saving.**

### Step 3 — Save draft
```
python tools/save_draft.py \
  --platform twitter \
  --content "<tweet text>" \
  --hashtags "#Tag1" "#Tag2" \
  --topic "<topic>"
```

### Step 4 — Present for approval
Show the tweet and character count:
> "Tweet ({char_count}/280): '{tweet text}'"
> "[draft id: {id}] — Ready to schedule?"

**Never publish without explicit approval.**

---

## Validation Checks
- [ ] Character count ≤ 280 (enforced in `publish_twitter.py`)
- [ ] No more than 2 hashtags
- [ ] No @mentions of strangers (considered spam)
- [ ] No "RT if you agree" or "Follow for more" patterns
- [ ] Draft platform = "twitter" in saved file

## Error Handling
- Research rate-limited → write from general knowledge; note it's unverified
- Tweet over 280 chars → identify and remove the least-essential clause
- `save_draft.py` error → verify `.tmp/drafts/` exists

## Lessons Learned
- Tweets with no hashtags often outperform hashtagged ones — test both
- The first 60 characters determine whether someone clicks "Show more" — lead with the hook, not context
- Questions get more replies; statements get more retweets — choose based on goal
- Optimal posting window: 9-11am and 5-7pm local time for target audience
- Avoid posting the same tweet twice — Twitter penalises duplicate content
