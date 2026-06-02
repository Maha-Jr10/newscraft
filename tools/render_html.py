"""
Renders the final newsletter HTML from content JSON + infographic images.
Prefers PNG (email-safe) over SVG. Gmail blocks SVG in emails.
Usage: python render_html.py <content_json>
Output: .tmp/newsletter.html
"""

import sys
import os
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()


def _cid_or_none(index: int) -> str | None:
    """Return a CID reference if the PNG exists — Gmail renders cid: but strips data: URIs."""
    png = Path(".tmp") / f"infographic_{index}.png"
    return f"cid:infographic_{index}" if png.exists() else None


def render(content_path: str, output_path: str | None = None) -> str:
    content = json.loads(Path(content_path).read_text(encoding="utf-8"))

    for i, section in enumerate(content.get("sections", [])):
        section["infographic_uri"] = _cid_or_none(i + 1)

    newsletter_name = os.environ.get("NEWSLETTER_NAME", "The Brief")

    env = Environment(loader=FileSystemLoader("templates"), autoescape=True)
    template = env.get_template("newsletter.html.j2")
    html = template.render(newsletter_name=newsletter_name, **content)

    if output_path is None:
        output_path = Path(".tmp") / "newsletter.html"

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"HTML rendered -> {output_path}")
    return html


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_html.py <content_json>")
        sys.exit(1)
    render(sys.argv[1])
