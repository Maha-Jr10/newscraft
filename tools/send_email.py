"""
Sends the rendered newsletter HTML via Resend API.
Attaches infographic PNGs as inline CID images (the only approach Gmail renders).
Usage: python send_email.py <html_file> "<subject>" [recipient_email]
Requires: RESEND_API_KEY, EMAIL_FROM, EMAIL_RECIPIENT in .env
"""

import sys
import os
import base64
from pathlib import Path
import resend
from dotenv import load_dotenv

load_dotenv()


def _inline_attachments() -> list[dict]:
    """Collect all infographic PNGs from .tmp/ as inline CID attachments."""
    attachments = []
    for png in sorted(Path(".tmp").glob("infographic_*.png")):
        idx = png.stem.split("_")[-1]
        attachments.append({
            "filename": png.name,
            "content": base64.b64encode(png.read_bytes()).decode("utf-8"),
            "content_type": "image/png",
            "content_id": f"infographic_{idx}",
        })
    return attachments


def send(html_path: str, subject: str, to_email: str | None = None) -> dict:
    resend.api_key = os.environ["RESEND_API_KEY"]

    html = Path(html_path).read_text(encoding="utf-8")
    from_addr = os.environ["EMAIL_FROM"]
    recipient = to_email or os.environ["EMAIL_RECIPIENT"]

    attachments = _inline_attachments()
    print(f"  Attaching {len(attachments)} inline image(s)...")

    response = resend.Emails.send({
        "from": from_addr,
        "to": recipient,
        "subject": subject,
        "html": html,
        "attachments": attachments,
    })

    print(f"Sent! ID: {response['id']}  ->  {recipient}")
    return response


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage: python send_email.py <html_file> "<subject>" [recipient]')
        sys.exit(1)
    html_file = sys.argv[1]
    subject = sys.argv[2]
    recipient = sys.argv[3] if len(sys.argv) > 3 else None
    send(html_file, subject, recipient)
