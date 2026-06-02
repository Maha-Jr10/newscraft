# Workflow: Create LinkedIn Post

## Objective
Research a topic (or use existing content) and produce a polished LinkedIn post saved as a draft, ready for review and scheduling.

## How the Work is Divided

| Layer | Who does it | What they do |
|---|---|---|
| Research (optional) | `tools/research_topic.py` | Fetch supporting facts and context |
| Writing | Claude (the agent) | Write the post — human expertise stays here |
| Saving | `tools/save_draft.py` | Persist the draft deterministically |

## Required Inputs

| Input | Description | Default |
|---|---|---|
| `topic` | What the post is about | — (required) |
| `tone` | Writing style | `"professional and insightful"` |
| `hashtags` | Relevant hashtag list | Agent selects 3-5 relevant tags |
| `research` | Whether to fetch fresh data | `true` |
| `source` | Optional existing content to reference | `null` |

## Outputs
- `.tmp/drafts/{id}.json` — saved LinkedIn draft
- Draft ID printed to console for use in scheduling

## Execution Steps

### Step 1 — Research (skip if topic is well-known or source content is provided)
```
python tools/research_topic.py "<topic>" 5
```
- 5 results is sufficient for a single post; saves to `.tmp/research.json`

### Step 2 — Write the post (agent does this)

Read `.tmp/research.json` if available, then write a LinkedIn post with these rules:

**Format:**
- **Hook (line 1):** Provocative statement, question, or surprising stat — no "I'm excited to share"
- **Body (2-4 short paragraphs):** Key insight, evidence, implication. One idea per paragraph. No waffle.
- **CTA (final line):** Question or prompt that invites engagement
- **Hashtags:** 3-5 relevant tags on a separate line at the end

**Constraints:**
- Total length: 150–800 characters (sweet spot: 300-500)
- No bullet-point lists in the opening hook
- No generic openers: "In today's world...", "As we all know...", "I'm thrilled to..."
- Use first person — LinkedIn is personal by nature

**Quality check before saving:**
- Does the first sentence make a reader stop scrolling?
- Is there one clear takeaway?
- Is the CTA specific (not just "What do you think?")?

### Step 3 — Save draft
```
python tools/save_draft.py \
  --platform linkedin \
  --content "<post text>" \
  --hashtags "#Tag1" "#Tag2" "#Tag3" \
  --topic "<topic>"
```
- Output: Draft saved with a new 8-char ID

### Step 4 — Present for approval
Show the post text to the user and ask:
> "Ready to schedule this LinkedIn post? [draft id: {id}]"

**Never schedule without explicit approval.**

---

## Validation Checks
- [ ] Character count ≤ 3,000 (LinkedIn hard limit)
- [ ] At least 1 hashtag included
- [ ] Hook does not start with "I am", "I'm excited", or "Thrilled to"
- [ ] CTA present in final line
- [ ] Draft status = "draft" in saved file

## Error Handling
- Research fails (429/timeout) → proceed with agent's existing knowledge; note lack of fresh data
- `save_draft.py` write error → check `.tmp/drafts/` directory exists; `mkdir -p .tmp/drafts`
- Post too long → trim body paragraphs; keep hook and CTA intact

## Lessons Learned
- Posts between 150-300 chars get 18% higher engagement on LinkedIn than posts > 1,000 chars
- Avoid posting on Friday afternoons or weekends — LinkedIn engagement drops sharply
- Numbering insights ("3 things I learned about X") consistently outperforms prose lists
- Hashtags beyond 5 reduce reach — LinkedIn's algorithm treats over-tagging as spam
