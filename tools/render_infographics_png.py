"""
Data-driven PNG infographic generator using Pillow.
Reads content from section["infographic_data"] in content.json.
No Cairo/system deps needed — Pillow only.
Usage: python render_infographics_png.py <content_json>
Output: .tmp/infographic_N.png
"""

import sys
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 560, 260

BG      = (240, 244, 255)
PRIMARY = (67,  97,  238)
DARK    = (15,  14,  23)
ACCENT  = (114, 9,   183)
MUTED   = (148, 163, 184)
WHITE   = (255, 255, 255)
LGRAY   = (226, 232, 240)
SUBTLE  = (71,  85,  105)

COLOR_MAP = {
    "primary": PRIMARY, "accent": ACCENT, "dark": DARK,
    "muted": MUTED, "subtle": SUBTLE, "white": WHITE,
}


def _fonts():
    weights = {"bold": "C:/Windows/Fonts/segoeuib.ttf", "reg": "C:/Windows/Fonts/segoeui.ttf"}
    sizes   = {"xl": 48, "lg": 22, "md": 14, "sm": 11, "xs": 10}
    f = {}
    for w, path in weights.items():
        for s, size in sizes.items():
            key = f"{w}_{s}"
            try:    f[key] = ImageFont.truetype(path, size)
            except: f[key] = ImageFont.load_default(size=size)
    return f


F = _fonts()


def _tc(d, text, cx, cy, font, fill):
    """Draw text centered at (cx, cy)."""
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((cx - bb[0] - tw // 2, cy - bb[1] - th // 2), text, font=font, fill=fill)


def _col(name: str):
    return COLOR_MAP.get(name, PRIMARY)


def _arrow_line(d, x1, y1, x2, y2, color, width=2):
    """Line + filled arrowhead pointing toward (x2, y2)."""
    d.line([(x1, y1), (x2, y2)], fill=color, width=width)
    dx, dy = x2 - x1, y2 - y1
    L = (dx**2 + dy**2) ** 0.5
    if L < 1:
        return
    ux, uy = dx / L, dy / L
    b1 = (x2 - ux*11 - uy*6, y2 - uy*11 + ux*6)
    b2 = (x2 - ux*11 + uy*6, y2 - uy*11 - ux*6)
    d.polygon([(x2, y2), b1, b2], fill=color)


# ── stat_highlight ──────────────────────────────────────────────────────────
def make_stats(data: dict) -> Image.Image:
    img   = Image.new("RGB", (W, H), BG)
    d     = ImageDraw.Draw(img)
    title = data.get("title", "KEY STATISTICS")
    stats = data.get("stats", [])[:3]

    _tc(d, title, W // 2, 18, F["bold_xs"], MUTED)

    card_w = 162
    gap    = (W - 3 * card_w) // 4
    xs     = [gap, gap * 2 + card_w, gap * 3 + card_w * 2]
    colors = [PRIMARY, ACCENT, PRIMARY]

    for i, (x, stat) in enumerate(zip(xs, stats)):
        accent = colors[i]
        d.rounded_rectangle([x, 36, x + card_w, 232], radius=12, fill=DARK)
        d.rounded_rectangle([x, 36, x + card_w, 42],  radius=3,  fill=accent)
        _tc(d, stat.get("number",   ""),  x + card_w // 2, 102, F["bold_xl"], accent)
        _tc(d, stat.get("label",    ""),  x + card_w // 2, 140, F["reg_sm"],  WHITE)
        _tc(d, stat.get("sublabel", ""),  x + card_w // 2, 158, F["reg_sm"],  WHITE)
        _tc(d, stat.get("caption",  ""),  x + card_w // 2, 208, F["reg_xs"],  SUBTLE)

    return img


# ── diagram: vertical architecture stack ────────────────────────────────────
def make_stack(data: dict) -> Image.Image:
    img    = Image.new("RGB", (W, H), BG)
    d      = ImageDraw.Draw(img)
    title  = data.get("title", "ARCHITECTURE STACK")
    layers = data.get("layers", [])

    _tc(d, title, W // 2, 16, F["bold_xs"], MUTED)

    n       = len(layers)
    pad_x   = 20
    lw      = W - 2 * pad_x
    arr_h   = 10
    total_h = H - 28 - 8
    lh      = (total_h - (n - 1) * arr_h) // n

    sub_colors = {
        "dark": (150, 150, 170), "highlight": (120, 140, 210),
        "primary": (190, 210, 255), "accent": (215, 175, 255),
    }

    y = 28
    for i, layer in enumerate(layers):
        color_key = layer.get("color", "dark")
        highlight = color_key == "highlight"
        bg_col    = DARK if highlight else _col(color_key)
        fg_col    = PRIMARY if highlight else WHITE
        sub_col   = sub_colors.get(color_key, MUTED)

        d.rounded_rectangle([pad_x, y, pad_x + lw, y + lh], radius=8, fill=bg_col)
        if highlight:
            d.rounded_rectangle([pad_x, y, pad_x + lw, y + lh], radius=8, outline=PRIMARY, width=2)

        label = layer.get("label", "")
        sub   = layer.get("sub", "")
        cy    = y + lh // 2
        if sub:
            _tc(d, label, W // 2, cy - 9,  F["bold_sm"], fg_col)
            _tc(d, sub,   W // 2, cy + 10, F["reg_xs"],  sub_col)
        else:
            _tc(d, label, W // 2, cy, F["bold_sm"], fg_col)

        # Downward arrow to next layer
        if i < n - 1:
            ax    = W // 2
            ay1   = y + lh + 1
            ay_tip = y + lh + arr_h
            d.line([(ax, ay1), (ax, ay_tip - 4)], fill=PRIMARY, width=2)
            d.polygon([(ax, ay_tip), (ax - 5, ay_tip - 4), (ax + 5, ay_tip - 4)], fill=PRIMARY)

        y += lh + arr_h

    return img


# ── chart: horizontal bars ───────────────────────────────────────────────────
def make_chart(data: dict) -> Image.Image:
    img      = Image.new("RGB", (W, H), BG)
    d        = ImageDraw.Draw(img)
    title    = data.get("title", "")
    subtitle = data.get("subtitle", "")
    bars     = data.get("bars", [])

    d.text((20, 14), title,    font=F["bold_md"], fill=DARK)
    d.text((20, 32), subtitle, font=F["reg_xs"],  fill=MUTED)

    max_bar_w = 340
    row_h     = 40
    y_start   = 55
    lbl_gap   = 14

    for i, bar in enumerate(bars):
        y      = y_start + i * row_h
        color  = _col(bar.get("color", "primary"))
        bw     = int(bar.get("pct", 50) / 100 * max_bar_w)
        value  = bar.get("value", "")
        label  = bar.get("label", "")

        d.text((20, y), label, font=F["reg_xs"], fill=SUBTLE)
        y_bar = y + lbl_gap
        d.rounded_rectangle([20, y_bar, 20 + max_bar_w, y_bar + 22], radius=5, fill=LGRAY)
        if bw > 4:
            d.rounded_rectangle([20, y_bar, 20 + bw, y_bar + 22], radius=5, fill=color)
        _tc(d, value, 20 + max_bar_w + 32, y_bar + 11, F["bold_sm"], color)

    return img


# ── timeline ─────────────────────────────────────────────────────────────────
def make_timeline(data: dict) -> Image.Image:
    img    = Image.new("RGB", (W, H), BG)
    d      = ImageDraw.Draw(img)
    title  = data.get("title", "TIMELINE")
    nodes  = data.get("nodes", [])
    footer = data.get("footer", "")

    _tc(d, title, W // 2, 18, F["bold_xs"], MUTED)

    n    = len(nodes)
    pad  = 60
    step = (W - 2 * pad) // max(n - 1, 1)
    cy   = 120
    r    = 24

    d.line([(pad, cy), (W - pad, cy)], fill=LGRAY, width=4)

    for i, node in enumerate(nodes):
        cx    = pad + i * step
        color = _col(node.get("color", "primary"))
        label = node.get("label", "")
        lines = node.get("lines", [])
        below = node.get("below", i % 2 == 1)

        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        _tc(d, label, cx, cy, F["reg_xs"], WHITE)

        if below:
            base_y = cy + r + 14
            if lines:
                _tc(d, lines[0], cx, base_y,      F["bold_xs"], DARK)
            if len(lines) > 1:
                _tc(d, lines[1], cx, base_y + 16, F["reg_xs"],  SUBTLE)
        else:
            base_y = cy - r - 22
            if len(lines) > 1:
                _tc(d, lines[0], cx, base_y - 8,  F["bold_xs"], DARK)
                _tc(d, lines[1], cx, base_y + 8,  F["reg_xs"],  SUBTLE)
            elif lines:
                _tc(d, lines[0], cx, base_y, F["bold_xs"], DARK)
            d.line([(cx, base_y + 18), (cx, cy - r)], fill=MUTED, width=1)

    if footer:
        _tc(d, footer, W // 2, 244, F["reg_xs"], MUTED)

    return img


# ── diagram: 2x2 grid (fallback for agent-loop style) ────────────────────────
def make_2x2_grid(data: dict) -> Image.Image:
    img   = Image.new("RGB", (W, H), BG)
    d     = ImageDraw.Draw(img)
    title = data.get("title", "THE FOUR PILLARS")
    nodes = data.get("nodes", [
        {"label": "REASON", "sub": "Multi-step logic",    "pos": "tl", "color": "dark"},
        {"label": "PLAN",   "sub": "Sequence goals",      "pos": "tr", "color": "dark"},
        {"label": "ACT",    "sub": "Tool execution",      "pos": "br", "color": "accent"},
        {"label": "MEMORY", "sub": "Retain state",        "pos": "bl", "color": "dark"},
    ])

    _tc(d, title, W // 2, 18, F["bold_xs"], MUTED)

    pos_map = {
        "tl": (30, 42, 200, 68), "tr": (330, 42, 200, 68),
        "br": (330, 150, 200, 68), "bl": (30, 150, 200, 68),
    }
    arrows = [(230,76,330,76),(430,110,430,150),(330,184,230,184),(130,150,130,110)]
    for x1, y1, x2, y2 in arrows:
        _arrow_line(d, x1, y1, x2, y2, PRIMARY)

    for node in nodes:
        x, y, w, h = pos_map.get(node.get("pos", "tl"), (30, 42, 200, 68))
        bg  = _col(node.get("color", "dark"))
        fg  = PRIMARY if node.get("color") == "dark" else WHITE
        d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=bg)
        _tc(d, node.get("label", ""), x + w // 2, y + h // 2 - 9,  F["bold_md"], fg)
        _tc(d, node.get("sub",   ""), x + w // 2, y + h // 2 + 11, F["reg_xs"],  MUTED)

    _tc(d, "AGENT LOOP",        W // 2, 124, F["bold_xs"], MUTED)
    _tc(d, "runs continuously", W // 2, 140, F["reg_xs"],  MUTED)
    return img


def make_diagram(data: dict) -> Image.Image:
    return make_stack(data) if "layers" in data else make_2x2_grid(data)


GENERATORS = {
    "diagram":        make_diagram,
    "stat_highlight": make_stats,
    "chart":          make_chart,
    "timeline":       make_timeline,
}


def render_png(content_path: str) -> list:
    content = json.loads(Path(content_path).read_text(encoding="utf-8"))
    outputs = []
    for i, section in enumerate(content.get("sections", [])):
        inf_type = section.get("infographic_type", "none")
        inf_data = section.get("infographic_data", {})
        if inf_type not in GENERATORS:
            outputs.append(None)
            continue
        print(f"  [{i+1}] Drawing {inf_type}...")
        img = GENERATORS[inf_type](inf_data)
        out = Path(".tmp") / f"infographic_{i + 1}.png"
        img.save(str(out), "PNG")
        outputs.append(str(out))
        print(f"       Saved -> {out}")
    return outputs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_infographics_png.py <content_json>")
        sys.exit(1)
    render_png(sys.argv[1])
