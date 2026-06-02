# contentcraft

> An agentic AI content studio built on the WAT framework. Research a topic, write the content, design infographics, publish a newsletter, and post to LinkedIn — all from a single prompt inside Claude Code.

---

## What It Does

One prompt. Full pipeline.

```
"Write a newsletter about the future of data engineering"
"Write a LinkedIn post about Claude Code"
"Repurpose the last newsletter for LinkedIn"
"Plan this week's content calendar"
```

Claude Code handles everything:

| Capability | What happens |
|---|---|
| **Newsletter** | Research → write → infographics → HTML email → deliver |
| **LinkedIn post** | Research → write → save draft → publish to your profile |
| **Long-form LinkedIn** | Write structured multi-section posts up to 3,000 chars |
| **Draft management** | Save, list, filter, and update drafts before publishing |
| **Content scheduling** | Schedule drafts to a calendar with optimal posting times |
| **Analytics** | Fetch engagement metrics per post, generate performance reports |
| **Content calendar** | Plan a full week of posts across platforms with slot management |

---

## Architecture: The WAT Framework

This project is built on the **WAT pattern** — Workflows, Agents, Tools.

```
┌──────────────────────────────────────────────────────────────┐
│  WORKFLOWS  (workflows/*.md)                                  │
│  Plain-language SOPs — objective, steps, edge cases,         │
│  lessons learned. The agent reads these, not code.           │
└──────────────────────────┬───────────────────────────────────┘
                           │ instructs
┌──────────────────────────▼───────────────────────────────────┐
│  AGENT  (Claude Code — you are talking to it right now)      │
│  Reads workflows, makes decisions, writes content,           │
│  calls tools in sequence, handles failures, asks questions   │
└──┬──────────┬───────────┬──────────┬──────────┬─────────────┘
   │          │           │          │          │
research   save_       publish_   fetch_     manage_
_topic     draft       linkedin   analytics  calendar
Tavily     .tmp/       LinkedIn   LinkedIn   .tmp/
           drafts/     API        API        calendar
```

**Why this works:** When AI handles every step directly, errors compound — 5 steps at 90% accuracy = 59% end-to-end reliability. The WAT pattern separates probabilistic reasoning (agent) from deterministic execution (tools). Each tool is a Python script: consistent, testable, and fast.

**The agent never publishes without your approval.** Every publish workflow has an explicit approval gate.

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Research | [Tavily](https://tavily.com) | AI-native web search, cleaner than scraping |
| AI / Writing | Claude Code (agent) | All content, decisions, coordination |
| Infographics | [Pillow](https://python-pillow.org) | Data-driven PNG generation, no system deps |
| Email HTML | [Jinja2](https://jinja.palletsprojects.com) | Responsive email template rendering |
| Email delivery | [Resend](https://resend.com) | CID inline images, reliable Gmail delivery |
| LinkedIn | [LinkedIn UGC API](https://developer.linkedin.com) | Post to personal profile or company page |
| Twitter/X | [Tweepy](https://tweepy.org) | Single tweets and threaded posts |

**No Anthropic API key required.** Claude Code *is* the AI layer — content, infographics, and decisions are produced directly by the agent.

---

## Capabilities

### Newsletter Pipeline
Research any topic → write structured sections → auto-generate custom infographics → render email-safe HTML → deliver via Resend.

Infographic types (data-driven, generated per section):
- `stat_highlight` — large number callout cards
- `diagram` — architecture stacks and flow diagrams  
- `chart` — horizontal bar charts with benchmarks
- `timeline` — horizontal milestone timelines

### LinkedIn Publishing
Write and publish directly to your personal LinkedIn profile via the UGC Posts API. Supports single posts and long-form structured posts up to 3,000 characters.

### Draft System
Every piece of content is saved as a JSON draft before publishing. Drafts track platform, status, character count, hashtags, publish metadata, and post URL.

```
draft statuses: draft → scheduled → published | failed
```

### Content Calendar
Generate a weekly content calendar with platform-optimal posting slots. Link drafts to slots, track status across the week.

### Analytics & Reporting
Fetch post-level engagement metrics (impressions, likes, comments, shares, engagement rate) and aggregate into markdown performance reports with benchmark comparisons.

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Maha-Jr10/contentcraft.git
cd contentcraft
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure API keys

Create a `.env` file (use `.env.example` as reference):

```env
# Research
TAVILY_API_KEY=

# Email delivery
RESEND_API_KEY=
EMAIL_FROM=onboarding@resend.dev
EMAIL_RECIPIENT=you@example.com
NEWSLETTER_NAME=The Brief

# LinkedIn
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_PERSON_URN=urn:li:person:YOUR_ID

# Twitter/X (optional — free tier requires credits)
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
TWITTER_BEARER_TOKEN=
```

### 3. Where to get each key

| Key | Source | Free tier |
|---|---|---|
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) | 1,000 searches/month |
| `RESEND_API_KEY` | [resend.com](https://resend.com) | 3,000 emails/month |
| `LINKEDIN_ACCESS_TOKEN` | [developer.linkedin.com](https://developer.linkedin.com) | Free — expires every 60 days |
| `LINKEDIN_PERSON_URN` | `GET https://api.linkedin.com/v2/userinfo` → `sub` field | — |
| Twitter keys | [developer.twitter.com](https://developer.twitter.com) | Requires credits for writes |

**LinkedIn setup:** Create a developer app, request *Share on LinkedIn* + *Sign In with OpenID Connect* products, generate an OAuth 2.0 token with scope `w_member_social openid profile`.

---

## Usage

Open this project in [Claude Code](https://claude.ai/code) and talk to it:

### Newsletter
```
Write a newsletter about <topic>
```

### LinkedIn
```
Write a LinkedIn post about <topic>
Write a long-form LinkedIn post about <topic>
Repurpose the last newsletter for LinkedIn
```

### Planning
```
Plan this week's content calendar
Show me all my drafts
Schedule draft <id> for tomorrow at 9am
```

### Analytics
```
Fetch analytics for my last LinkedIn post
Generate a performance report for this week
```

---

## Project Structure

```
contentcraft/
├── tools/
│   ├── research_topic.py          # Tavily web search → .tmp/research.json
│   ├── save_draft.py              # Create/update drafts in .tmp/drafts/
│   ├── list_drafts.py             # List/filter drafts by platform and status
│   ├── schedule_post.py           # Schedule drafts → .tmp/schedule.json
│   ├── publish_linkedin.py        # Post to LinkedIn via UGC Posts API
│   ├── publish_twitter.py         # Post single tweet or thread via Tweepy
│   ├── fetch_analytics.py         # Pull engagement metrics from APIs
│   ├── generate_report.py         # Aggregate analytics → markdown report
│   ├── manage_calendar.py         # Create/view/update weekly content calendar
│   ├── render_infographics_png.py # Data-driven PNG infographics (Pillow)
│   ├── render_html.py             # Jinja2 HTML rendering → .tmp/newsletter.html
│   └── send_email.py              # Resend API with CID inline attachments
├── templates/
│   └── newsletter.html.j2         # Responsive email template
├── workflows/
│   ├── newsletter.md              # Newsletter end-to-end pipeline
│   ├── create_linkedin_post.md    # LinkedIn post creation SOP
│   ├── create_twitter_post.md     # Single tweet creation SOP
│   ├── create_twitter_thread.md   # Twitter thread creation SOP
│   ├── repurpose_content.md       # Cross-platform content repurposing
│   ├── schedule_content.md        # Draft scheduling SOP
│   ├── publish_content.md         # Publishing with approval gate
│   ├── social_analytics.md        # Analytics fetching and reporting
│   └── content_calendar.md        # Weekly calendar planning SOP
├── .tmp/                          # Generated files — gitignored, regenerated each run
│   ├── drafts/                    # Draft JSON files
│   ├── analytics/                 # Analytics JSON files
│   └── schedule.json              # Content schedule
├── .env                           # API keys — never commit this
├── requirements.txt
├── CLAUDE.md                      # WAT framework agent instructions
└── README.md
```

---

## Key Design Decisions

**Why no Anthropic API key?**
Claude Code itself is the agent. All writing, planning, and design decisions happen inside the Claude Code session — no separate API calls, no extra cost beyond your Claude subscription.

**Why CID inline attachments for email images?**
Gmail blocks both SVG `<img>` tags and `data:` base64 URIs. CID (Content-ID) attachments are the only cross-client approach that reliably renders in Gmail, Outlook, and Apple Mail.

**Why Pillow instead of cairosvg for infographics?**
`cairosvg` and `svglib` require the Cairo system DLL, which is not available on Windows without installing GTK3. Pillow is pure Python and works everywhere.

**Why no auto-publish on schedule?**
The schedule file is a planning artefact. Publishing requires explicit approval each time — intentional safety gate. For cloud-based auto-publishing, connect to GitHub Actions or use a dedicated scheduler like Buffer.

---

## Requirements

- Python 3.11+
- [Claude Code](https://claude.ai/code)
- Tavily API key (for research)
- Resend API key (for newsletter email)
- LinkedIn Developer App (for LinkedIn publishing)

---

## License

MIT
