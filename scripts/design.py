"""Shared design tokens and SVG helpers for the profile README assets.

Every panel in /assets is drawn from these tokens so the whole README reads
as one system. Change a colour here, re-run the scripts, and everything follows.
"""
from html import escape

# Canonical panel width. GitHub's README column is ~830-900px, so drawing at
# 900 keeps text close to 1:1 instead of being scaled down and blurry.
W = 900

C = {
    "bg": "#07070D",
    "card": "#0C0C16",
    "card2": "#11111E",
    "line": "#1F1F35",
    "text": "#EEEEF8",
    "sub": "#A6A6C0",
    "mute": "#6C6C88",
    "violet": "#8B5CF6",
    "lilac": "#C4B5FD",
    "cyan": "#22D3EE",
    "sky": "#67E8F9",
    "pink": "#F472B6",
    "rose": "#FB7185",
    "green": "#4ADE80",
    "amber": "#FBBF24",
}

# System font stacks only: SVGs rendered through <img> cannot load web fonts.
SANS = ("'Segoe UI Variable Display','Segoe UI',-apple-system,BlinkMacSystemFont,"
        "Inter,'Helvetica Neue',Ubuntu,Arial,sans-serif")
MONO = ("'JetBrains Mono','Cascadia Code','SF Mono',SFMono-Regular,Menlo,Consolas,"
        "'Liberation Mono',monospace")

# Approximate advance widths, used to size pills and typing clips.
MONO_W = 0.6    # em per monospace glyph
SANS_W = 0.56   # em per average sans glyph

BASE_CSS = f"""
.sans{{font-family:{SANS}}}
.mono{{font-family:{MONO}}}
.in{{animation:rise .6s cubic-bezier(.2,.7,.2,1) both}}
@keyframes rise{{from{{opacity:0;transform:translateY(6px)}}}}
.blink{{animation:blink 1.05s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def esc(s: str) -> str:
    return escape(s, quote=True)


def svg(w: int, h: int, body: str, *, title: str, css: str = "", defs: str = "") -> str:
    """Wrap a body in a complete, accessible SVG document."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" fill="none" role="img" aria-label="{esc(title)}">\n'
        f"<title>{esc(title)}</title>\n"
        f"<style>{BASE_CSS}{css}</style>\n"
        f"<defs>{defs}</defs>\n{body}\n</svg>\n"
    )


def card_defs(w: int, h: int, rx: int = 20, uid: str = "c") -> str:
    """Clip path + hairline gradient border shared by every card."""
    return f"""
<clipPath id="{uid}-clip"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>
<linearGradient id="{uid}-edge" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{C['violet']}" stop-opacity=".75"/>
  <stop offset=".45" stop-color="{C['line']}" stop-opacity=".9"/>
  <stop offset="1" stop-color="{C['cyan']}" stop-opacity=".55"/>
</linearGradient>
<radialGradient id="{uid}-spot" cx="0" cy="0" r="1">
  <stop offset="0" stop-color="#fff" stop-opacity=".06"/>
  <stop offset="1" stop-color="#fff" stop-opacity="0"/>
</radialGradient>"""


def card_open(w: int, h: int, rx: int = 20, uid: str = "c") -> str:
    return (f'<g clip-path="url(#{uid}-clip)">'
            f'<rect width="{w}" height="{h}" fill="{C["card"]}"/>'
            f'<ellipse cx="0" cy="0" rx="{w * .6:.0f}" ry="{h * .9:.0f}" fill="url(#{uid}-spot)"/>')


def card_close(w: int, h: int, rx: int = 20, uid: str = "c") -> str:
    return (f'</g><rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx - .5}" '
            f'fill="none" stroke="url(#{uid}-edge)"/>')


def eyebrow(x: float, y: float, num: str, label: str, color: str = C["violet"]) -> str:
    """Small mono section label, e.g. `02 / WHAT I DO`."""
    return (f'<text x="{x}" y="{y}" class="mono" font-size="11" letter-spacing="2.2" '
            f'fill="{color}">{esc(num)}<tspan fill="{C["mute"]}"> / </tspan>{esc(label)}</text>')


def pill(x: float, y: float, label: str, *, color: str, size: float = 11,
         mono: bool = True, h: float = 24, pad: float = 11, dot: bool = False) -> tuple[str, float]:
    """A rounded tag. Returns (svg, width) so callers can lay pills out in a row."""
    cw = (MONO_W if mono else SANS_W) * size
    tw = len(label) * cw + (len(label) * 0.6 if mono else 0)
    dw = 12 if dot else 0
    w = tw + pad * 2 + dw
    cls = "mono" if mono else "sans"
    out = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
           f'fill="{color}" fill-opacity=".08" stroke="{color}" stroke-opacity=".32"/>')
    if dot:
        out += f'<circle cx="{x + pad + 3:.1f}" cy="{y + h / 2:.1f}" r="3" fill="{color}"/>'
    out += (f'<text x="{x + pad + dw:.1f}" y="{y + h / 2 + size * .36:.1f}" class="{cls}" '
            f'font-size="{size}" letter-spacing="{.6 if mono else 0}" fill="{color}">{esc(label)}</text>')
    return out, w
