# Workflow: Schedule Content for Publishing

## Objective
Schedule one or more existing drafts for future publishing at optimal times. Updates the draft status and the central schedule file.

## How the Work is Divided

| Layer | Who does it | What they do |
|---|---|---|
| Draft review | Agent | Confirms the draft is ready to schedule |
| Scheduling | `tools/schedule_post.py` | Writes to `.tmp/schedule.json`, patches draft |
| Verification | `tools/schedule_post.py view` | Confirms scheduled items |

## Required Inputs

| Input | Description | Default |
|---|---|---|
| `draft_id` | ID of the draft to schedule | — (required) |
| `publish_at` | Target datetime (ISO format) | — (required) |
| `platform` | For validation | Read from draft |

**Publish_at format:** `YYYY-MM-DDTHH:MM:SS` e.g. `2025-06-10T09:00:00`

## Outputs
- `.tmp/schedule.json` updated with new entry
- Draft status updated to `"scheduled"`
- Confirmation printed to console

## Execution Steps

### Step 1 — Review the draft
```
python tools/list_drafts.py --status draft
```
Confirm the target draft exists and its content is approved.

### Step 2 — Determine optimal posting time
If the user has not specified a time, suggest based on platform:

**LinkedIn optimal windows (based on engagement data):**
- Tuesday–Thursday: 08:00–10:00
- Monday/Friday: 10:00–11:00
- Avoid: weekends, after 18:00

**Twitter optimal windows:**
- Weekdays: 09:00, 12:00, 17:00
- Weekends: 11:00–13:00
- Avoid: Monday 07:00–09:00 (low engagement)

Ask: "Post at {suggested_time}? Or specify a different datetime."

### Step 3 — Schedule the post
```
python tools/schedule_post.py <draft_id> <publish_at>
```
Example:
```
python tools/schedule_post.py a3f1b2c4 2025-06-10T09:00:00
```

### Step 4 — Confirm
```
python tools/schedule_post.py view
```
Show the full schedule and confirm the new entry appears correctly.

---

## Validation Checks
- [ ] Draft status = "draft" before scheduling (not already published or failed)
- [ ] `publish_at` is in the future
- [ ] `publish_at` is a valid ISO datetime
- [ ] No duplicate: the same draft is not already scheduled for another time
- [ ] Schedule file created/updated at `.tmp/schedule.json`

## Error Handling
- Draft not found → run `list_drafts.py` to find the correct ID
- Datetime in the past → ask user for a future datetime; suggest tomorrow at 09:00
- Draft already scheduled → confirm reschedule: "Draft {id} is already scheduled for {time}. Reschedule to {new_time}?"
- Schedule file corrupted → delete `.tmp/schedule.json` and re-schedule from scratch

## Lessons Learned
- Always confirm the schedule after adding — the view command catches mis-parsed datetimes
- Scheduling too many posts on the same day reduces reach per post; aim for max 1 LinkedIn + 3 Twitter per day
- The schedule file does NOT auto-publish — it is a planning artefact; a separate publish step is always required
- `schedule_post.py` validates that the time is in the future; if testing, use a real future date
