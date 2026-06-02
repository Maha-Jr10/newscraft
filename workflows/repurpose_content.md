# Workflow: Repurpose Content for Social Media

## Objective
Take a piece of long-form content (newsletter, blog post, research, or any `.tmp/content.json`) and extract its highest-value insights into platform-specific social media drafts without repeating research.

## How the Work is Divided

| Layer | Who does it | What they do |
|---|---|---|
| Content reading | Agent | Reads and analyses the source content |
| Adaptation | Agent | Rewrites for each platform's format and constraints |
| Saving | `tools/save_draft.py` | Saves each draft independently |

**Key principle:** Repurposing is NOT copying. Each piece must be rewritten for the platform's voice, format, and audience expectation.

## Required Inputs

| Input | Description | Default |
|---|---|---|
| `source` | Path to content file OR raw text | `.tmp/content.json` (newsletter) |
| `platforms` | Which platforms to create for | `["linkedin", "twitter", "twitter_thread"]` |
| `topic` | Overriding topic label | Read from source content |
| `tone_linkedin` | LinkedIn tone | `"professional and insightful"` |
| `tone_twitter` | Twitter tone | `"sharp and direct"` |

## Outputs
- One `.tmp/drafts/{id}.json` per platform per content piece
- Draft IDs logged for easy reference

## Execution Steps

### Step 1 — Read the source content
If `source = .tmp/content.json`, read it directly.
If `source` is a URL, run:
```
python tools/research_topic.py "<url or topic>" 3
```
If `source` is raw text, the agent reads it from the user message.

Extract from the source:
- **3-5 key insights** — the most surprising, contrarian, or actionable points
- **1 key stat** — the most compelling number
- **Core argument** — the single sentence that captures the piece's thesis
- **Target audience** — who would most benefit from reading this

### Step 2 — Create LinkedIn post (agent writes this)

Apply `create_linkedin_post.md` format rules to the extracted insights:
- Hook = the most surprising insight or stat from the source
- Body = 2-3 sentences expanding the core argument
- CTA = question that connects the topic to the reader's role
- Hashtags = 3-5 tags relevant to the topic

Then save:
```
python tools/save_draft.py --platform linkedin --content "<post>" --hashtags "..." --topic "<topic>"
```

### Step 3 — Create Twitter hook tweet (agent writes this)

Best-performing repurpose pattern: distil the core stat or argument into a single punchy tweet.
Apply `create_twitter_post.md` format rules.

```
python tools/save_draft.py --platform twitter --content "<tweet>" --topic "<topic>"
```

### Step 4 — Create Twitter thread (agent writes this)

Use the 3-5 key insights extracted in Step 1 as the thread body. Each insight = one tweet.

Structure:
- Tweet 1: Hook — the core argument in one sentence
- Tweets 2-N: One insight each, with brief evidence
- Final tweet: "The bottom line: [one sentence]" + original source link

Apply `create_twitter_thread.md` validation rules.

Save as a list:
```
python tools/save_draft.py --platform twitter_thread --content '[...]' --topic "<topic>"
```

### Step 5 — Present all drafts
List all created drafts with their IDs:
```
python tools/list_drafts.py --status draft
```

Show a summary:
> "Created 3 drafts from '{source}':
> - LinkedIn post [id: xxx]
> - Twitter tweet [id: xxx]
> - Twitter thread [id: xxx]
>
> Ready to schedule any of these?"

**Never schedule without explicit approval per draft.**

---

## Validation Checks
- [ ] Each draft has a distinct angle — not the same text reformatted
- [ ] LinkedIn post does NOT start with the same hook as the Twitter tweet
- [ ] All tweets in thread are ≤ 280 chars
- [ ] Source is credited in thread's final tweet (link or attribution)
- [ ] All drafts saved with matching `topic` in metadata

## Error Handling
- Source file not found → ask user to provide the content directly
- Content too thin to repurpose (< 200 words) → run `research_topic.py` to enrich it first
- Platform content overlaps too much → rewrite with a different angle; use `create_linkedin_post.md` for guidance

## Lessons Learned
- The best repurposed content takes the most counter-intuitive finding and leads with it
- Never use the newsletter headline as the LinkedIn hook — audiences overlap; they've seen it
- One strong Twitter thread from a newsletter consistently drives more newsletter subscribers than the newsletter itself
- Repurposing same-day as publishing the original gets the best cross-platform reach
- Do not repurpose every newsletter — only those with a stat or argument strong enough to stand alone
