# Workflow: Create Twitter/X Thread

## Objective
Write a multi-tweet thread that explores a topic in depth, saves it as a single draft, and prepares it for sequential publishing.

## How the Work is Divided

| Layer | Who does it | What they do |
|---|---|---|
| Research | `tools/research_topic.py` | Required — threads need substance |
| Writing | Claude (the agent) | Structure and write the full thread |
| Saving | `tools/save_draft.py` | Save thread as a list of tweets |
| Publishing | `tools/publish_twitter.py` | Posts tweets as a reply chain |

## Required Inputs

| Input | Description | Default |
|---|---|---|
| `topic` | Thread subject | — (required) |
| `length` | Number of tweets | 5-8 (sweet spot) |
| `format` | Thread structure | `"numbered"` — see formats below |
| `hashtags` | Tags for the first tweet | 1-2 max |

**Thread formats:**
- `numbered` — "1/ Hook\n\n2/ Point\n\n3/ Point..."
- `narrative` — Story arc with no numbers
- `listicle` — Each tweet is one item in a list
- `breakdown` — Explain a concept step-by-step

## Outputs
- `.tmp/drafts/{id}.json` — platform: `twitter_thread`, content: `list[str]`

## Execution Steps

### Step 1 — Research
```
python tools/research_topic.py "<topic>" 8
```
Threads need at least 3-5 credible supporting points. Run research before writing.

### Step 2 — Write the thread (agent does this)

**Thread architecture:**

```
Tweet 1 (Hook):   The most compelling sentence you can write.
                  Make a bold claim or ask a sharp question.
                  Hint at what's coming: "Here's what I found: 🧵"
                  Target: 200-240 chars

Tweets 2-N-1:     Each tweet = one standalone idea.
                  Could be read alone and still make sense.
                  End each with a subtle bridge to the next.
                  Target: 200-260 chars each

Tweet N (Close):  Summary or takeaway + CTA.
                  "The thread in one sentence: ___"
                  Or a question that provokes replies.
                  Target: 150-220 chars
```

**Per-tweet rules:**
- Each tweet ≤ 280 characters (hard limit)
- Numbered format: start each tweet with "N/" (e.g., "1/", "2/")
- No "likes/RTs appreciated" in any tweet
- Hashtags only on the first tweet (2 max)

**Content rules:**
- One insight per tweet — never split a single idea across two tweets
- Use concrete examples, not abstractions
- Data > opinions wherever possible

After writing the full thread, count characters for each tweet before saving.

### Step 3 — Save draft
The `content` field must be a JSON array of tweet strings:

```
python tools/save_draft.py \
  --platform twitter_thread \
  --content '["1/ Hook tweet...", "2/ Point one...", "3/ Point two...", "4/ Closing takeaway..."]' \
  --hashtags "#Tag1" \
  --topic "<topic>"
```

> Note: For multi-tweet content, write the content.json file directly or use `save_draft.py` programmatically with the Python API.

### Step 4 — Preview
Display all tweets in sequence with character counts:
```
Tweet 1 (230/280): 1/ Hook text...
Tweet 2 (245/280): 2/ Second point...
...
```

Ask user: "This thread has {N} tweets. Ready to schedule? [draft id: {id}]"

**Never publish without explicit approval.**

---

## Validation Checks
- [ ] Each tweet ≤ 280 characters
- [ ] Minimum 3 tweets, maximum 25 (Twitter thread limit)
- [ ] First tweet is the strongest hook
- [ ] No tweet references "the previous tweet" (each must stand alone)
- [ ] Hashtags only on tweet 1
- [ ] Draft platform = "twitter_thread", content is a list

## Error Handling
- Any tweet > 280 chars → identify it, trim the least essential phrase
- Thread too short (<3 tweets) → expand or convert to a single tweet workflow
- Save fails for JSON array content → write draft JSON file directly to `.tmp/drafts/`
- Rate limit during publishing → `publish_twitter.py` uses `wait_on_rate_limit=True`; it will auto-pause

## Lessons Learned
- Threads with 5-7 tweets get the best completion rates; beyond 10 the drop-off is steep
- The first tweet determines 80% of the thread's reach — spend most editing time there
- Adding a "here's the full breakdown" summary tweet at the end increases saves/bookmarks
- Do not post a thread as individual replies manually — use `publish_twitter.py` to ensure the reply chain is correctly formed
- Posting a thread and then quoting it from your account increases impressions by ~30%
