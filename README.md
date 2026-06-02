# newscraft

> An agentic AI pipeline that researches a topic, writes newsletter content, generates custom infographics, and delivers a polished HTML email — all from a single prompt.

---

## What It Does

Tell it a topic. It handles the rest:

1. **Researches** the web for the latest, most relevant sources (Tavily)
2. **Writes** the newsletter — structured sections, compelling copy, key stats (Claude Code agent)
3. **Designs** custom infographics for each section (Pillow — charts, timelines, stat cards, diagrams)
4. **Renders** a responsive, email-safe HTML template (Jinja2)
5. **Delivers** to your inbox with inline images that actually render in Gmail (Resend)

---

## Architecture: The WAT Framework

This project follows the **WAT pattern** — Workflows, Agents, Tools:

```
┌─────────────────────────────────────────────────────┐
│  WORKFLOW  (workflows/newsletter.md)                 │
│  Plain-language SOP — objective, steps, edge cases  │
└─────────────────────┬───────────────────────────────┘
                      │ instructs
┌─────────────────────▼───────────────────────────────┐
│  AGENT  (Claude Code)                               │
│  Reads the workflow, makes decisions, calls tools   │
│  Writes content + SVG designs directly              │
└──────┬──────────────┬──────────────┬────────────────┘
       │              │              │
┌──────▼──────┐ ┌─────▼──────┐ ┌────▼─────────────────┐
│  research   │ │  render    │ │  send_email.py        │
│  _topic.py  │ │  _infogra  │ │  Resend API           │
│  Tavily API │ │  phics.py  │ │                       │
└─────────────┘ │  Pillow    │ └──────────────────────┘
                └─────┬──────┘
                ┌─────▼──────┐
                │ render_    │
                │ html.py    │
                │ Jinja2     │
                └────────────┘
```

**Why this separation matters:** When AI handles every step directly, accuracy compounds downward — 5 steps at 90% each = 59% end-to-end success. By offloading deterministic execution to Python scripts, the agent stays focused on reasoning and coordination.

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Research | [Tavily](https://tavily.com) | AI-native web search — cleaner than scraping |
| AI / Writing | Claude Code (agent) | Content, structure, infographic design |
| Infographics | [Pillow](https://python-pillow.org) | PNG generation — no Cairo/system deps |
| HTML rendering | [Jinja2](https://jinja.palletsprojects.com) | Responsive email template |
| Email delivery | [Resend](https://resend.com) | Reliable delivery, CID inline images |

**No Anthropic API key required.** Claude Code *is* the AI layer — content and infographic designs are produced directly by the agent, not via separate API calls.

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/your-username/newscraft.git
cd newscraft
python -m venv .venv
.venv/Scripts/activate      # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure your API keys

Copy `.env` and fill in your keys:

```env
TAVILY_API_KEY=your_tavily_api_key_here
RESEND_API_KEY=your_resend_api_key_here
EMAIL_FROM=onboarding@resend.dev      # or your verified domain
EMAIL_RECIPIENT=you@example.com
NEWSLETTER_NAME=The Brief
```

| Key | Where to get it | Free tier |
|---|---|---|
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) | 1,000 searches/month |
| `RESEND_API_KEY` | [resend.com](https://resend.com) | 3,000 emails/month |

> **Note on `EMAIL_FROM`:** Resend requires a verified sending domain for production. For testing, `onboarding@resend.dev` works out of the box.

---

## Usage

Open this project in [Claude Code](https://claude.ai/code) and run:

```
Write a newsletter about <your topic>
```

Claude will run the full pipeline and ask for your approval before sending.

**Examples:**
```
Write a newsletter about the future of data engineering
Write a newsletter about breakthroughs in quantum computing
Write a newsletter about the state of open source AI in 2025
```

### Running tools manually

Each step can also be run independently:

```bash
# 1. Research
python tools/research_topic.py "your topic" 10

# 2. (Agent writes .tmp/content.json directly)

# 3. Generate infographics
python tools/render_infographics_png.py .tmp/content.json

# 4. Render HTML
python tools/render_html.py .tmp/content.json

# 5. Send
python tools/send_email.py .tmp/newsletter.html "Your Subject Line"
```

---

## Project Structure

```
newscraft/
├── tools/
│   ├── research_topic.py          # Tavily web research → .tmp/research.json
│   ├── render_infographics_png.py # Pillow PNG generator (data-driven)
│   ├── render_html.py             # Jinja2 HTML renderer → .tmp/newsletter.html
│   └── send_email.py              # Resend API with CID inline attachments
├── templates/
│   └── newsletter.html.j2         # Responsive email template
├── workflows/
│   └── newsletter.md              # SOP: objective, steps, edge cases, lessons learned
├── .tmp/                          # Generated files (gitignored — regenerated each run)
├── .env                           # API keys (gitignored)
├── requirements.txt
└── CLAUDE.md                      # Agent instructions (WAT framework)
```

---

## Infographic Types

The generator supports four data-driven infographic types, automatically chosen per section:

| Type | Use case | Example |
|---|---|---|
| `stat_highlight` | Key numbers that anchor the story | $3.1T / 56% / 80% |
| `diagram` | Architecture stacks or flow relationships | Raw Data → DE → AI Apps |
| `chart` | Comparative metrics, trends | Skill demand shifts |
| `timeline` | Role/product/market evolution | ETL Dev → AI Architect |

Each infographic is generated from structured data in `content.json` — no hardcoded visuals.

---

## Email Rendering Notes

Getting images to render in Gmail requires a specific approach:

| Method | Gmail support |
|---|---|
| `<img src="...svg">` | Blocked — Gmail strips SVG |
| `<img src="data:image/png;base64,...">` | Blocked — Gmail strips `data:` URIs |
| **CID inline attachments** (`cid:name`) | **Works** — standard MIME spec |

This project uses CID inline attachments. PNGs are attached to the email and referenced as `cid:infographic_1` etc. in the HTML.

---

## Requirements

- Python 3.11+
- Claude Code (the agent)
- Tavily API key
- Resend API key

---

## License

MIT
