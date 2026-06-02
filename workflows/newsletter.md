# Workflow: Generate & Send Newsletter

## Objective
Given a topic, produce a polished HTML newsletter with infographics and deliver it via email.

## How the Work is Divided

| Layer | Who does it | What they do |
|---|---|---|
| Research | `tools/research_topic.py` (Tavily) | Fetch real web content — agent can't browse |
| Writing & SVGs | Claude (the agent) | Content, structure, SVG infographic code |
| Rendering | `tools/render_html.py` (Jinja2) | Deterministic HTML assembly |
| Delivery | `tools/send_email.py` (Resend) | SMTP is infrastructure, not reasoning |

**The agent does the AI work directly. No Anthropic API key is needed.**

## Required Inputs
| Input | Description | Default |
|---|---|---|
| `topic` | What the newsletter is about | — (required) |
| `tone` | Writing style | `"professional but engaging"` |
| `send` | Whether to email after rendering | `false` — always ask first |

## Pipeline

### Step 1 — Research
```
python tools/research_topic.py "<topic>" 10
```
- Calls Tavily `search_depth="advanced"`, fetches 10 sources
- Output: `.tmp/research.json` with `topic`, `answer`, and `sources[]`

**Edge cases:**
- `TAVILY_API_KEY` missing → abort, ask user to set it in `.env`
- Zero results → try a broader/rephrased query
- Rate limit (429) → wait 10s, retry once

---

### Step 2 — Write Content (agent does this)
Read `.tmp/research.json` and produce `.tmp/content.json` with this schema:

```json
{
  "subject_line": "under 60 chars",
  "preview_text": "under 90 chars",
  "headline": "main headline",
  "intro": "2-3 sentences",
  "sections": [
    {
      "headline": "section headline",
      "body": "paragraphs separated by \\n\\n",
      "infographic_type": "chart | diagram | timeline | stat_highlight | none",
      "infographic_description": "what to visualise, or null"
    }
  ],
  "key_stat": {
    "number": "e.g. 73% or $4.2B",
    "label": "short label",
    "context": "one sentence"
  },
  "outro": "1-2 sentence sign-off",
  "sources": ["url1", "url2"]
}
```

- 3-4 sections, at least 2 with infographics
- Save directly to `.tmp/content.json`

---

### Step 3 — Generate Infographics (agent does this)
For each section where `infographic_type != "none"`:
- Write raw SVG code: `width="560" height="260" viewBox="0 0 560 260"`
- Colour palette: bg `#f0f4ff`, primary `#4361ee`, dark `#0f0e17`, accent `#7209b7`
- Save each as `.tmp/infographic_1.svg`, `.tmp/infographic_2.svg`, …

**Edge cases:**
- If a section has `infographic_type: "none"`, skip it — the render step handles missing SVGs gracefully

---

### Step 4 — Render HTML
```
python tools/render_html.py .tmp/content.json
```
- Reads `content.json` + any `.tmp/infographic_*.svg` files
- Embeds SVGs as base64 data URIs (self-contained, no external hosting)
- Output: `.tmp/newsletter.html`

**Edge cases:**
- Missing SVG → section renders without an infographic (no crash)
- File >100KB → Gmail may clip it; warn user if large

---

### Step 5 — Preview & Approve
Read `.tmp/newsletter.html`, show the content to the user, and ask:
> "Ready to send to [EMAIL_RECIPIENT]? Subject: [subject_line]"

**Never send without explicit user approval.**

---

### Step 6 — Send
```
python tools/send_email.py .tmp/newsletter.html "<subject_line>"
```
- Reads all `.tmp/infographic_*.png` files and attaches them as **inline CID attachments**
- HTML references them as `cid:infographic_1`, `cid:infographic_2`, etc.
- Output: Resend email ID logged to console

**Edge cases:**
- `RESEND_API_KEY` missing → abort, direct user to resend.com
- `EMAIL_FROM` domain not verified → use `onboarding@resend.dev` for testing
- No PNG files in `.tmp/` → images won't show; run `render_infographics_png.py` first

---

## Notes & Lessons Learned
- Tavily `search_depth="advanced"` costs 2 credits vs 1 for basic — worth it for quality
- No Anthropic API key needed — the agent (Claude Code) handles all AI reasoning directly
- Resend free tier: 3,000 emails/month, 100/day
- `EMAIL_FROM` must match a verified domain in Resend; `onboarding@resend.dev` works for dev/testing
- **Gmail blocks SVG images entirely** — do not use `<img src="...svg">` in emails
- **Gmail also strips `data:` URIs** — `data:image/png;base64,...` does not render either
- **CID inline attachments are the only reliable approach** — attach PNGs to the email and reference as `cid:name` in HTML. This is the standard MIME spec and works in Gmail, Outlook, Apple Mail
- `cairosvg` and `svglib` both require the Cairo system DLL which is not available on Windows without GTK3 — use Pillow (`render_infographics_png.py`) instead
- Print statements using `→` (U+2192) crash on Windows cp1252 terminals — use `->` instead
