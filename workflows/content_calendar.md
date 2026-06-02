# Workflow: Content Calendar Planning

## Objective
Plan a week or month of social media content, create a structured calendar with platform slots, assign topics to each slot, and generate drafts ready for review.

## How the Work is Divided

| Layer | Who does it | What they do |
|---|---|---|
| Calendar structure | `tools/manage_calendar.py` | Creates slots at optimal times |
| Topic planning | Agent | Assigns themes and angles to each slot |
| Content creation | Agent + `tools/save_draft.py` | Writes and saves each draft |
| Linking | `tools/manage_calendar.py update` | Links draft IDs to calendar slots |

## Required Inputs

| Input | Description | Default |
|---|---|---|
| `week` | ISO week string | Current week |
| `theme` | Overarching content theme for the week | Derived from newsletter topic |
| `linkedin_slots` | Number of LinkedIn posts | `3` |
| `twitter_slots` | Number of tweets/threads | `5` |
| `research_topics` | Whether to research each topic | `true` for threads, `false` for tweets |

## Outputs
- `.tmp/calendar_{year}_{week}.json` — structured calendar with slots
- One `.tmp/drafts/{id}.json` per planned post
- Summary of all drafts and their calendar positions

## Execution Steps

### Step 1 — Create the calendar structure
```
python tools/manage_calendar.py create --week 2025-W23 --linkedin 3 --twitter 5
```

View what was created:
```
python tools/manage_calendar.py view --week 2025-W23
```

### Step 2 — Plan topics (agent does this)

Read the calendar slots. For each slot, assign a topic based on:
- The week's overarching theme
- Platform-specific angle (LinkedIn = professional depth, Twitter = sharp + timely)
- Variety rule: no two consecutive posts on the same sub-topic
- Mix rule: aim for 50% educational, 30% opinion, 20% engagement/question

**Topic planning heuristics:**
- Monday: Set the week's theme with a bold statement or question
- Tuesday/Wednesday: Deep-dive LinkedIn posts (highest weekday engagement)
- Thursday: Thread — synthesise the week's insights
- Friday: Lighter engagement post or prediction for the following week
- Weekend (Twitter only): Community question or reframe of a popular narrative

For each slot, record: `{date} | {platform} | {topic} | {angle}`

### Step 3 — Research each topic (where needed)
For each thread topic (worth full research):
```
python tools/research_topic.py "<slot topic>" 5
```
Save to `.tmp/research_{slot_date}.json` to avoid overwriting between slots.

### Step 4 — Create drafts
Follow the appropriate workflow per platform:
- LinkedIn slots → `create_linkedin_post.md`
- Twitter single → `create_twitter_post.md`
- Twitter threads → `create_twitter_thread.md`

Save each draft, note the returned draft ID.

### Step 5 — Link drafts to calendar slots
For each draft created:
```
python tools/manage_calendar.py update \
  --week 2025-W23 \
  --slot <slot_index> \
  --topic "<topic>" \
  --draft-id <draft_id>
```

### Step 6 — Review calendar
```
python tools/manage_calendar.py view --week 2025-W23
```

Show the completed calendar to the user and ask:
> "Calendar complete for week 2025-W23. {N} drafts ready.
> Ready to schedule any of these? Or would you like to review individual drafts first?"

**Never schedule without per-draft approval.**

---

## Validation Checks
- [ ] Calendar file exists at `.tmp/calendar_{week}.json`
- [ ] All slots have a topic assigned (no "empty" status remaining)
- [ ] All slots with draft_id have a matching file in `.tmp/drafts/`
- [ ] No two slots publish on the same platform within 4 hours of each other
- [ ] Content variety: max 2 posts on the same sub-topic in one week

## Error Handling
- `manage_calendar.py create` fails → check `.tmp/` directory exists; `mkdir -p .tmp`
- Week string invalid → use format `YYYY-W##` e.g. `2025-W23` (zero-pad the week number)
- Draft creation fails partway through → calendar slots remain with `status: empty`; resume from the failed slot
- Topic list runs thin → run `research_topic.py` on the week's theme for 10 results; derive sub-topics from the sources

## Lessons Learned
- Planning a full week at once produces more coherent content than ad-hoc posting — use this workflow weekly
- The calendar structure optimal posting times are suggestions; adjust for your audience's timezone
- Do not create all drafts in one session if the week covers different topics — space them out so each benefits from fresh research
- The calendar is ephemeral (`.tmp/`); export it to a permanent location (Google Sheets, Notion) before the week ends if you need historical planning records
- Use `repurpose_content.md` for at least one slot per week — repurposing a strong newsletter consistently outperforms fresh-written social content
