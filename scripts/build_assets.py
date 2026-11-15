"""Build the static SVG panels used by README.md.

    python scripts/build_assets.py

Edit the CONTENT section below, re-run, commit /assets. Needs network access
once per run to pull icons from skillicons.dev (MIT-licensed) into stack.svg.
Stats are separate: see render_stats.py, which a GitHub Action runs daily.
"""
from __future__ import annotations

import math
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from design import (C, MONO_W, SANS_W, W, card_close, card_defs, card_open, esc,  # noqa: E402
                    eyebrow, pill, svg)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

# ─────────────────────────────── CONTENT ────────────────────────────────
NAME = "Youssef Y. Younis"
HANDLE = "@0xJarmenKell"
LOCATION = "Cairo, Egypt"
EMAIL = "youssefyousry994@gmail.com"

ROLES = [
    "Founder & CTO @ Techverse",
    "Software Development Engineer II",
    "Full-Stack · Angular · React · Node.js",
    "DevSecOps & Security Engineering",
    "Secure systems, shipped with craft.",
]

HERO_TAGS = [("LEADERSHIP", C["violet"]), ("FULL-STACK", C["cyan"]),
             ("DEVSECOPS", C["pink"]), ("SECURITY R&D", C["green"])]

ABOUT_YAML = [  # (key, [(text, colour-key), ...])
    ("location", [("Cairo, Egypt", "text")]),
    ("background", [("Computer Science", "text"), (" · ", "mute"),
                    ("Networks & Systems Administration", "text")]),
    ("craft", [("secure, scalable web platforms", "text"), (" — ", "mute"),
               ("architecture to production", "text")]),
    ("stack", [("[ ", "mute"), ("TypeScript, Angular, React, Next.js, Node.js, Rails", "sky"),
               (" ]", "mute")]),
    ("currently", [("leading engineering ", "text"), ("@ Techverse", "lilac")]),
    ("open_to", [("[ ", "mute"), ("collaborations, consulting, senior engineering roles", "sky"),
                 (" ]", "mute")]),
]

FOCUS = [
    ("Engineering Leadership", "violet", "layers",
     ["Founder & CTO at Techverse.", "Turning product vision into",
      "scalable architecture — and", "leading the teams that ship it."],
     "STRATEGY · ARCHITECTURE · TEAMS"),
    ("Full-Stack Engineering", "cyan", "code",
     ["Angular, React & Next.js on", "Node.js, Express, Rails and",
      "Supabase back-ends: platforms,", "dashboards and marketplaces."],
     "TYPESCRIPT · APIS · PRODUCT UX"),
    ("Security & DevSecOps", "pink", "shield",
     ["Roots in networks & sys-admin.", "CI/CD with Docker & Jenkins,",
      "hardened APIs, and red-team", "research that informs defense."],
     "HARDENING · CI/CD · RED TEAM"),
]

STACK = [
    ("LANGUAGES", "violet", "ts,js,py,go,ruby,php,cs,nim,bash,powershell"),
    ("FRONTEND", "cyan", "angular,react,nextjs,redux,tailwind,sass,bootstrap,html,css,vite,webpack"),
    ("BACKEND & DATA", "pink", "nodejs,express,rails,prisma,supabase,postgres,mongodb"),
    ("DEVOPS & CLOUD", "green", "docker,jenkins,linux,git,github,netlify"),
    ("DESIGN & TOOLING", "amber", "figma,xd,vscode,vitest"),
]

PROJECTS = [  # file, title, repo, badge, accent, description lines (<=52 chars), chips
    ("devhouse", "DevHouse Platform", "Devhouse-website", "MONOREPO", "violet",
     ["TypeScript monorepo powering DevHouse.LTD — a",
      "Next.js i18n web app and a hardened Express API",
      "with Prisma, Zod validation, Helmet & rate limits."],
     ["Next.js", "Express", "Prisma", "Zod", "Vitest"]),
    ("wptique", "WPtique Marketplace", "wptique-marketplace", "PRODUCT", "cyan",
     ["Digital marketplace for themes, plugins & code —",
      "Stripe checkout, subscription tiers, licensing,",
      "reviews and a complete admin dashboard."],
     ["React", "TypeScript", "Supabase", "Stripe", "Tailwind"]),
    ("digital-bond", "Digital Bond", "Digital-Bond", "LIVE", "pink",
     ["Official website for a digital marketing &",
      "software house agency — engineered as a fast,",
      "component-driven Angular 17 single-page app."],
     ["Angular", "TypeScript", "CSS", "Netlify"]),
    ("maids", "Maids.cc Admin Dashboard", "maids.cc-tech", "ADMIN", "amber",
     ["Angular admin dashboard with user management,",
      "dynamic data rendering and instant filtering —",
      "built clean, typed and component-first."],
     ["Angular", "TypeScript", "HTML/CSS"]),
    ("cms", "Client Management System", "Client-Management-System", "FULL-STACK", "green",
     ["Server-rendered CRM to manage clients end to end",
      "— MongoDB persistence via Mongoose and serverless",
      "deployment on Netlify Functions."],
     ["Node.js", "Express", "MongoDB", "EJS"]),
    ("offensive-nim", "Offensive Security R&D", "Offensive_Nim", "RED TEAM", "rose",
     ["Hands-on research into adversary tradecraft —",
      "tooling in Nim, Go, PowerShell & C# to understand",
      "attacks deeply and engineer stronger defenses."],
     ["Nim", "Go", "PowerShell", "C#"]),
]

BUTTONS = [("portfolio", "Portfolio", "globe", "violet"), ("resume", "Résumé", "doc", "cyan"),
           ("linkedin", "LinkedIn", "linkedin", "lilac"), ("email", "Email", "mail", "pink"),
           ("blog", "Blog", "pen", "green")]
# ────────────────────────────────────────────────────────────────────────


def write(rel: str, content: str) -> None:
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"  wrote assets/{rel}  ({len(content.encode()) / 1024:.1f} KB)")


def discrete_anim(attr: str, events: list[tuple[float, float]], total: float) -> str:
    """SMIL discrete animation from (time_s, value) events over a looping timeline."""
    pts: list[tuple[float, float]] = []
    if not events or events[0][0] > 0:
        pts.append((0.0, 0.0))
    for t, v in events:
        kt = round(t / total, 5)
        if pts and kt <= pts[-1][0]:
            pts[-1] = (pts[-1][0], v)
        else:
            pts.append((kt, v))
    kts = ";".join(f"{k:g}" for k, _ in pts)
    vals = ";".join(f"{v:g}" for _, v in pts)
    return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{total:.2f}s" '
            f'repeatCount="indefinite" keyTimes="{kts}" values="{vals}"/>')


def ellipse_path(cx: float, cy: float, rx: float, ry: float, deg: float) -> str:
    th = math.radians(deg)
    x1, y1 = cx - rx * math.cos(th), cy - rx * math.sin(th)
    x2, y2 = cx + rx * math.cos(th), cy + rx * math.sin(th)
    return (f"M{x1:.1f} {y1:.1f}A{rx} {ry} {deg} 1 1 {x2:.1f} {y2:.1f}"
            f"A{rx} {ry} {deg} 1 1 {x1:.1f} {y1:.1f}Z")


# ───────────────────────────────── HERO ─────────────────────────────────
def build_hero() -> None:
    w, h = W, 360
    cx, cy = 742, 182
    x0, ry0, fs = 76, 236, 20          # typing line origin + font size
    cw = fs * MONO_W

    # Typing timeline: type → hold → delete → next role, looping forever.
    t, per_role, cursor = 0.0, [], []
    for r in ROLES:
        ev = []
        for k in range(len(r) + 1):
            ev.append((t + k * .055, k * cw))
        t += len(r) * .055 + 2.0
        for k in range(len(r) - 1, -1, -1):
            t += .024
            ev.append((t, k * cw))
        t += .35
        per_role.append(ev)
        cursor += [(tt, x0 + v + 3) for tt, v in ev]
    total = t

    defs = card_defs(w, h, 22, "h") + f"""
<linearGradient id="name" x1="48" y1="0" x2="540" y2="0" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#FFFFFF"/><stop offset=".55" stop-color="#DDD6FE"/>
  <stop offset="1" stop-color="{C['sky']}"/></linearGradient>
<linearGradient id="shine" x1="0" y1="0" x2="140" y2="0" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".75"/>
  <stop offset="1" stop-color="#fff" stop-opacity="0"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="-220 0;900 0;900 0"
    keyTimes="0;.45;1" dur="7s" repeatCount="indefinite"/></linearGradient>
<linearGradient id="core" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{C['lilac']}"/><stop offset="1" stop-color="{C['cyan']}"/></linearGradient>
<radialGradient id="fade" cx=".68" cy=".45" r=".7">
  <stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<mask id="gridmask"><rect width="{w}" height="{h}" fill="url(#fade)"/></mask>
<pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
  <path d="M30 0H0V30" stroke="#fff" stroke-opacity=".055"/></pattern>
<filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="55"/></filter>
<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".05"/>
  <stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>"""
    defs += "".join(
        f'<clipPath id="r{i}"><rect x="{x0 - 2}" y="{ry0 - 21}" height="30" '
        f'width="{(len(r) * cw + 4) if i == 0 else 0:.0f}">{discrete_anim("width", ev, total)}</rect></clipPath>'
        for i, (r, ev) in enumerate(zip(ROLES, per_role)))

    css = """
.a1{animation:d1 19s ease-in-out infinite alternate}
.a2{animation:d2 23s ease-in-out infinite alternate}
.a3{animation:d3 17s ease-in-out infinite alternate}
@keyframes d1{to{transform:translate(90px,50px)}}
@keyframes d2{to{transform:translate(-80px,60px)}}
@keyframes d3{to{transform:translate(70px,-50px)}}
.beam{animation:beam 9s ease-in-out infinite}
@keyframes beam{0%{transform:translateX(-400px) skewX(-20deg)}55%,100%{transform:translateX(1100px) skewX(-20deg)}}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 3.2s ease-out infinite}
.pulse.b{animation-delay:1.6s}
@keyframes pulse{from{transform:scale(1);opacity:.55}to{transform:scale(2.5);opacity:0}}
.dot{transform-box:fill-box;transform-origin:center;animation:dot 2s ease-in-out infinite}
@keyframes dot{50%{transform:scale(1.5);opacity:.6}}
.dash{animation:dash 30s linear infinite}.dash.r{animation-direction:reverse;animation-duration:44s}
@keyframes dash{to{stroke-dashoffset:-400}}
.tw{animation:tw 3.5s ease-in-out infinite}
@keyframes tw{50%{opacity:.15}}
.glow{animation:glow 4s ease-in-out infinite}
@keyframes glow{50%{opacity:.75}}
"""
    b = [card_open(w, h, 22, "h")]
    b.append(f'<rect width="{w}" height="{h}" fill="{C["bg"]}"/>')
    b.append(f'''<g filter="url(#blur)">
  <circle class="a1" cx="130" cy="20" r="150" fill="{C['violet']}" opacity=".5"/>
  <circle class="a2" cx="800" cy="110" r="140" fill="{C['cyan']}" opacity=".32"/>
  <circle class="a3" cx="470" cy="400" r="160" fill="{C['pink']}" opacity=".25"/></g>''')
    b.append(f'<rect width="{w}" height="{h}" fill="url(#grid)" mask="url(#gridmask)"/>')
    b.append(f'<rect class="beam" x="0" y="-40" width="260" height="{h + 80}" fill="url(#beam)"/>')

    # Status chip
    b.append(f'''<g class="in" style="animation-delay:.1s">
  <rect x="48" y="40" width="214" height="28" rx="14" fill="{C['green']}" fill-opacity=".08"
    stroke="{C['green']}" stroke-opacity=".35"/>
  <circle class="pulse" cx="65" cy="54" r="4" fill="{C['green']}"/>
  <circle cx="65" cy="54" r="4" fill="{C['green']}"/>
  <text x="78" y="58" class="mono" font-size="11" letter-spacing="1.6" fill="{C['green']}">OPEN TO OPPORTUNITIES</text></g>''')
    b.append(f'<text class="mono in" x="852" y="58" text-anchor="end" font-size="11" letter-spacing="2.2" '
             f'fill="{C["lilac"]}" opacity=".85" style="animation-delay:.2s">VIEW PORTFOLIO ↗</text>')

    # Name + shine sweep
    name = esc(NAME)
    b.append(f'<g class="in" style="animation-delay:.25s">'
             f'<text x="46" y="138" class="sans" font-size="52" font-weight="800" letter-spacing="-1.4" '
             f'fill="url(#name)">{name}</text>'
             f'<text x="46" y="138" class="sans" font-size="52" font-weight="800" letter-spacing="-1.4" '
             f'fill="url(#shine)">{name}</text></g>')
    b.append(f'<text x="49" y="174" class="mono in" font-size="15" style="animation-delay:.4s">'
             f'<tspan fill="{C["lilac"]}">{esc(HANDLE)}</tspan>'
             f'<tspan fill="{C["mute"]}" dx="10">·</tspan>'
             f'<tspan class="sans" fill="{C["sub"]}" dx="10" font-size="15.5">{esc(LOCATION)}</tspan></text>')

    # Typing roles
    b.append(f'<g class="in" style="animation-delay:.55s">'
             f'<text x="48" y="{ry0}" class="mono" font-size="{fs}" font-weight="700" fill="{C["cyan"]}">❯</text>')
    for i, r in enumerate(ROLES):
        # textLength pins the rendered width to our estimate, so the clip and the
        # cursor line up exactly whatever monospace font the viewer's OS supplies.
        b.append(f'<text x="{x0}" y="{ry0}" class="mono" font-size="{fs}" fill="{C["text"]}" '
                 f'textLength="{len(r) * cw:.1f}" lengthAdjust="spacing" '
                 f'clip-path="url(#r{i})">{esc(r)}</text>')
    b.append(f'<rect class="blink" x="{x0 + 3}" y="{ry0 - 17}" width="10" height="21" rx="1.5" '
             f'fill="{C["cyan"]}" opacity=".9">{discrete_anim("x", cursor, total)}</rect></g>')

    # Domain tags
    x = 48.0
    tags = []
    for label, col in HERO_TAGS:
        s, pw = pill(x, 286, label, color=col, size=10.5, dot=True)
        tags.append(s)
        x += pw + 8
    b.append(f'<g class="in" style="animation-delay:.7s">{"".join(tags)}</g>')

    # Orbit system
    orbits = [(150, 56, 14, C["violet"], "dash"), (112, 40, -22, C["cyan"], "dash r"),
              (78, 78, 0, C["lilac"], "dash")]
    b.append(f'<g class="in" style="animation-delay:.3s">')
    b.append(f'<circle class="glow" cx="{cx}" cy="{cy}" r="62" fill="{C["violet"]}" opacity=".45" filter="url(#soft)"/>')
    for rx, ryy, deg, col, cls in orbits:
        b.append(f'<path class="{cls}" d="{ellipse_path(cx, cy, rx, ryy, deg)}" stroke="{col}" '
                 f'stroke-opacity=".38" stroke-width="1.2" stroke-dasharray="3 7"/>')
    for r_ in (1, 2):
        b.append(f'<circle class="pulse{" b" if r_ == 2 else ""}" cx="{cx}" cy="{cy}" r="40" '
                 f'stroke="{C["lilac"]}" stroke-width="1.2"/>')

    travellers = [  # orbit index, glyph, colour, duration, begin offset
        (0, "TS", C["sky"], 16, 0), (0, "Go", C["cyan"], 16, -8),
        (1, "</>", C["lilac"], 11, -2), (1, "#!", C["pink"], 11, -7.5),
        (2, "{ }", C["green"], 9, -4)]
    for oi, glyph, col, dur, beg in travellers:
        rx, ryy, deg, _, _ = orbits[oi]
        cw_ = max(30, len(glyph) * 7 + 16)
        b.append(f'<g><animateMotion dur="{dur}s" begin="{beg}s" repeatCount="indefinite" '
                 f'path="{ellipse_path(cx, cy, rx, ryy, deg)}"/>'
                 f'<rect x="{-cw_ / 2}" y="-11" width="{cw_}" height="22" rx="7" fill="{C["card2"]}" '
                 f'stroke="{col}" stroke-opacity=".65"/>'
                 f'<text y="4" text-anchor="middle" class="mono" font-size="10.5" font-weight="700" '
                 f'fill="{col}">{esc(glyph)}</text></g>')
    for i, (dx, dy, dur, beg) in enumerate([(-150, 0, 7, 0), (112, -4, 5, -2)]):
        rx, ryy, deg, col, _ = orbits[i]
        b.append(f'<circle r="3" fill="{col}"><animateMotion dur="{dur}s" begin="{beg}s" '
                 f'repeatCount="indefinite" path="{ellipse_path(cx, cy, rx, ryy, deg)}"/></circle>')
    # Core drawn last so the travelling chips pass behind it (cheap depth cue).
    b.append(f'<circle cx="{cx}" cy="{cy}" r="40" fill="{C["card2"]}" stroke="url(#core)" stroke-width="1.6"/>')
    b.append(f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" class="mono" font-size="28" '
             f'font-weight="800" fill="url(#core)">0x</text>')
    b.append(f'<rect class="blink" x="{cx + 19}" y="{cy + 5}" width="8" height="2.5" fill="{C["cyan"]}"/>')
    b.append("</g>")

    for i, (sx, sy) in enumerate([(612, 70), (868, 112), (640, 300), (880, 268), (790, 52), (560, 330)]):
        b.append(f'<circle class="tw" cx="{sx}" cy="{sy}" r="1.3" fill="#fff" '
                 f'style="animation-delay:{i * .6:.1f}s"/>')

    b.append(card_close(w, h, 22, "h"))
    write("hero.svg", svg(w, h, "\n".join(b), title=f"{NAME} — {ROLES[0]} · {ROLES[1]}",
                          css=css, defs=defs))


# ─────────────────────────────── ABOUT ──────────────────────────────────
def build_about() -> None:
    w, h, fs = W, 372, 14
    cw = fs * MONO_W
    xp, xc, xv = 28, 50, 172          # prompt, content, yaml value columns
    defs = card_defs(w, h, 18, "a")

    def typed(text: str, y: float, start: float, uid: str) -> tuple[str, str]:
        step = .065
        ev = [(0, 0)] + [(start + k * step, k * cw + 2) for k in range(1, len(text) + 1)]
        ev.append((start + len(text) * step + .01, 800))
        dur = ev[-1][0] + .01
        kts = ";".join(f"{t / dur:.4f}" for t, _ in ev)
        vals = ";".join(f"{v:g}" for _, v in ev)
        clip = (f'<clipPath id="{uid}"><rect x="{xc - 2}" y="{y - 16}" height="22" width="800">'
                f'<animate attributeName="width" calcMode="discrete" dur="{dur:.2f}s" fill="freeze" '
                f'keyTimes="{kts}" values="{vals}"/></rect></clipPath>')
        line = (f'<text x="{xp}" y="{y}" class="mono in" font-size="{fs}" font-weight="700" '
                f'fill="{C["cyan"]}" style="animation-delay:{start - .25:.2f}s">❯</text>'
                f'<text x="{xc}" y="{y}" class="mono" font-size="{fs}" fill="{C["text"]}" '
                f'textLength="{len(text) * cw:.1f}" lengthAdjust="spacing" '
                f'clip-path="url(#{uid})">{esc(text)}</text>')
        return clip, line

    clip1, cmd1 = typed("whoami", 84, .45, "t1")
    clip2, cmd2 = typed("cat about.yml", 148, 1.7, "t2")
    defs += clip1 + clip2

    b = [card_open(w, h, 18, "a")]
    # Window chrome
    b.append(f'<rect width="{w}" height="42" fill="{C["card2"]}"/>'
             f'<path d="M0 42.5H{w}" stroke="{C["line"]}"/>')
    for i, col in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        b.append(f'<circle cx="{24 + i * 20}" cy="21" r="6" fill="{col}"/>')
    b.append(f'<text x="{w / 2}" y="25.5" text-anchor="middle" class="mono" font-size="12" '
             f'fill="{C["mute"]}">youssef@techverse: ~/about</text>')
    b.append(eyebrow(w - 28 - 88, 25.5, "01", "ABOUT"))

    b.append(cmd1)
    b.append(f'<text x="{xc}" y="111" class="mono in" font-size="{fs}" style="animation-delay:1.05s">'
             f'<tspan fill="{C["text"]}" font-weight="700">{esc(NAME)}</tspan>'
             f'<tspan fill="{C["mute"]}"> — </tspan><tspan fill="{C["lilac"]}">Founder &amp; CTO @ Techverse</tspan>'
             f'<tspan fill="{C["mute"]}"> · </tspan><tspan fill="{C["cyan"]}">Software Development Engineer II</tspan></text>')
    b.append(cmd2)
    y = 175
    for i, (key, segs) in enumerate(ABOUT_YAML):
        spans = "".join(f'<tspan fill="{C[c]}">{esc(t)}</tspan>' for t, c in segs)
        b.append(f'<text x="{xc}" y="{y}" class="mono in" font-size="{fs}" '
                 f'style="animation-delay:{2.75 + i * .13:.2f}s"><tspan fill="{C["violet"]}">{esc(key)}</tspan>'
                 f'<tspan fill="{C["mute"]}">:</tspan><tspan x="{xv}">{spans}</tspan></text>')
        y += 27
    b.append(f'<g class="in" style="animation-delay:3.7s">'
             f'<text x="{xp}" y="{y + 9}" class="mono" font-size="{fs}" font-weight="700" fill="{C["cyan"]}">❯</text>'
             f'<rect class="blink" x="{xc}" y="{y - 5}" width="9" height="18" rx="1" fill="{C["cyan"]}"/></g>')
    b.append(card_close(w, h, 18, "a"))
    write("about.svg", svg(w, h, "\n".join(b), defs=defs,
                           title=f"whoami: {NAME} — Founder & CTO @ Techverse, Software Development Engineer II, Cairo, Egypt"))


# ─────────────────────────────── FOCUS ──────────────────────────────────
ICONS = {
    "layers": '<path d="M20 9 31 15 20 21 9 15Z"/><path d="M9 20.5 20 26.5 31 20.5"/><path d="M9 26 20 32 31 26"/>',
    "code": '<path d="M15 14 9 20.5 15 27"/><path d="M25 14 31 20.5 25 27"/><path d="M22.5 11.5 17.5 29.5"/>',
    "shield": '<path d="M20 8.5 30 12.5V20c0 6-4.5 10-10 12-5.5-2-10-6-10-12v-7.5Z"/><path d="M15.5 20.5 19 24l6-7"/>',
}


def build_focus() -> None:
    w, h = W, 336
    defs = card_defs(w, h, 20, "f")
    for _, col, _, _, _ in FOCUS:
        defs += (f'<linearGradient id="g-{col}" x1="0" y1="0" x2="1" y2="1">'
                 f'<stop offset="0" stop-color="{C[col]}"/><stop offset="1" stop-color="{C[col]}" stop-opacity=".35"/>'
                 f'</linearGradient>')
    css = """.tile{animation:tile 4.5s ease-in-out infinite}
@keyframes tile{50%{opacity:.55}}"""
    b = [card_open(w, h, 20, "f"), eyebrow(28, 40, "02", "WHAT I DO")]
    b.append(f'<text x="28" y="72" class="sans" font-size="21" font-weight="700" fill="{C["text"]}">'
             f'From architecture to production — end to end.</text>')
    cw_, gap, y0, ch = 272, 16, 96, 214
    for i, (title, col, icon, lines, tags) in enumerate(FOCUS):
        x = 28 + i * (cw_ + gap)
        a = C[col]
        b.append(f'<g class="in" style="animation-delay:{.15 + i * .15:.2f}s">')
        b.append(f'<rect x="{x}" y="{y0}" width="{cw_}" height="{ch}" rx="14" fill="{C["card2"]}" '
                 f'stroke="{C["line"]}"/>')
        b.append(f'<path d="M{x + 14} {y0 + .5}H{x + 120}" stroke="{a}" stroke-width="1.5" opacity=".9"/>')
        b.append(f'<rect class="tile" x="{x + 18}" y="{y0 + 18}" width="44" height="44" rx="11" '
                 f'fill="{a}" opacity=".18" filter="none" style="animation-delay:{i * 1.2:.1f}s"/>')
        b.append(f'<rect x="{x + 20}" y="{y0 + 20}" width="40" height="40" rx="10" fill="url(#g-{col})"/>')
        b.append(f'<g transform="translate({x + 20} {y0 + 20})" stroke="#fff" stroke-width="1.9" '
                 f'stroke-linecap="round" stroke-linejoin="round">{ICONS[icon]}</g>')
        b.append(f'<text x="{x + 20}" y="{y0 + 92}" class="sans" font-size="16.5" font-weight="700" '
                 f'fill="{C["text"]}">{esc(title)}</text>')
        for j, ln in enumerate(lines):
            b.append(f'<text x="{x + 20}" y="{y0 + 117 + j * 20}" class="sans" font-size="13" '
                     f'fill="{C["sub"]}">{esc(ln)}</text>')
        b.append(f'<text x="{x + 20}" y="{y0 + ch - 20}" class="mono" font-size="9.5" letter-spacing="1.2" '
                 f'fill="{a}">{esc(tags)}</text></g>')
    b.append(card_close(w, h, 20, "f"))
    write("focus.svg", svg(w, h, "\n".join(b), css=css, defs=defs,
                           title="What I do: engineering leadership, full-stack engineering, security & DevSecOps"))


# ─────────────────────────────── STACK ──────────────────────────────────
def fetch_icon(slug: str) -> str:
    req = urllib.request.Request(f"https://skillicons.dev/icons?i={slug}",
                                 headers={"User-Agent": "profile-readme-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def nest_icon(raw: str, slug: str, x: float, y: float, size: float) -> str:
    """Re-root a skillicons SVG at (x, y) and namespace its ids to avoid collisions."""
    raw = raw.strip()
    ids = set(re.findall(r'id="([^"]+)"', raw))
    for i in ids:
        raw = raw.replace(f'id="{i}"', f'id="{slug}-{i}"').replace(f"url(#{i})", f"url(#{slug}-{i})")
        raw = raw.replace(f'href="#{i}"', f'href="#{slug}-{i}"')
    return re.sub(r"<svg\b[^>]*>", f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 256 256" fill="none">',
                  raw, count=1)


def build_stack() -> None:
    row_h, y0, size = 62, 100, 44
    w, h = W, y0 + len(STACK) * row_h + 14
    defs = card_defs(w, h, 20, "s")
    css = """.ic{transform-box:fill-box;transform-origin:center;animation:pop .55s cubic-bezier(.2,.9,.3,1.3) both}
@keyframes pop{from{opacity:0;transform:scale(.6)}}"""
    b = [card_open(w, h, 20, "s"), eyebrow(28, 40, "03", "TECH ARSENAL")]
    b.append(f'<text x="28" y="72" class="sans" font-size="21" font-weight="700" fill="{C["text"]}">'
             f'Tools I use to design, build, ship &amp; secure.</text>')
    n = 0
    cache: dict[str, str] = {}
    for r, (label, col, slugs) in enumerate(STACK):
        ry = y0 + r * row_h
        if r:
            b.append(f'<path d="M28 {ry}H{w - 28}" stroke="#fff" stroke-opacity=".05"/>')
        b.append(f'<rect x="28" y="{ry + row_h / 2 - 4}" width="8" height="8" rx="2" fill="{C[col]}"/>')
        b.append(f'<text x="46" y="{ry + row_h / 2 + 4}" class="mono" font-size="10.5" letter-spacing="1.8" '
                 f'fill="{C["sub"]}">{esc(label)}</text>')
        for i, slug in enumerate(slugs.split(",")):
            raw = cache.get(slug) or fetch_icon(slug)
            cache[slug] = raw
            b.append(f'<g class="ic" style="animation-delay:{.1 + n * .035:.2f}s">'
                     f'{nest_icon(raw, slug, 214 + i * 54, ry + (row_h - size) / 2, size)}</g>')
            n += 1
    b.append(card_close(w, h, 20, "s"))
    names = ", ".join(s for _, _, sl in STACK for s in sl.split(","))
    write("stack.svg", svg(w, h, "\n".join(b), css=css, defs=defs, title=f"Tech stack: {names}"))


# ─────────────────────────────── WORK ───────────────────────────────────
REPO_ICON = ('<path d="M3 2.5A1.5 1.5 0 0 1 4.5 1h10v13h-10A1.5 1.5 0 0 0 3 15.5Z"/>'
             '<path d="M3 15.5A1.5 1.5 0 0 0 4.5 17h10v-3"/><path d="M6.5 4.5h5"/>')


def build_work() -> None:
    # Section title bar
    w, h = W, 76
    b = [card_open(w, h, 18, "wt"), eyebrow(28, 31, "04", "SELECTED WORK")]
    b.append(f'<text x="28" y="57" class="sans" font-size="20" font-weight="700" fill="{C["text"]}">'
             f'Things I have designed, built &amp; shipped.</text>')
    b.append(f'<text x="{w - 28}" y="47" text-anchor="end" class="mono" font-size="11" letter-spacing="2" '
             f'fill="{C["lilac"]}">BROWSE ALL REPOSITORIES ↗</text>')
    b.append(card_close(w, h, 18, "wt"))
    write("work/title.svg", svg(w, h, "\n".join(b), defs=card_defs(w, h, 18, "wt"),
                                title="Selected work — browse all repositories"))

    w, h = 440, 200
    css = """.sheen{animation:sheen 6s ease-in-out infinite}
@keyframes sheen{0%{transform:translateX(-160px)}60%,100%{transform:translateX(480px)}}"""
    for i, (file, title, repo, badge, col, lines, chips) in enumerate(PROJECTS):
        a = C[col]
        defs = card_defs(w, h, 16, "p") + f"""
<radialGradient id="glow" cx="1" cy="0" r="1"><stop offset="0" stop-color="{a}" stop-opacity=".22"/>
  <stop offset="1" stop-color="{a}" stop-opacity="0"/></radialGradient>
<linearGradient id="top" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{a}" stop-opacity="0"/>
  <stop offset=".5" stop-color="{a}"/><stop offset="1" stop-color="{a}" stop-opacity="0"/></linearGradient>"""
        b = [card_open(w, h, 16, "p"),
             f'<rect width="{w}" height="{h}" fill="url(#glow)"/>',
             f'<rect class="sheen" x="0" y="0" width="160" height="1.5" fill="url(#top)" '
             f'style="animation-delay:{i * .7:.1f}s"/>',
             f'<g transform="translate(24 25)" stroke="{a}" stroke-width="1.6" stroke-linecap="round" '
             f'stroke-linejoin="round">{REPO_ICON}</g>',
             f'<text x="52" y="40" class="sans" font-size="17.5" font-weight="700" fill="{C["text"]}">{esc(title)}</text>',
             f'<text x="52" y="60" class="mono" font-size="11" fill="{C["mute"]}">0xJarmenKell/{esc(repo)}</text>']
        bw = len(badge) * (9.5 * MONO_W + .6) + 20
        s, _ = pill(w - 24 - bw, 24, badge, color=a, size=9.5, h=22, pad=10)
        b.append(s)
        for j, ln in enumerate(lines):
            b.append(f'<text x="24" y="{94 + j * 20}" class="sans" font-size="13.5" fill="{C["sub"]}">{esc(ln)}</text>')
        x = 24.0
        for chip in chips:
            s, cw_ = pill(x, 156, chip, color=C["sub"], size=10.5, h=24, pad=10)
            b.append(s)
            x += cw_ + 6
        b.append(card_close(w, h, 16, "p"))
        write(f"work/{file}.svg", svg(w, h, "\n".join(b), css=css, defs=defs,
                                       title=f"{title} — {' '.join(lines)}"))


# ───────────────────────────── BUTTONS ──────────────────────────────────
BTN_ICONS = {
    "globe": '<circle cx="9" cy="9" r="7.5"/><ellipse cx="9" cy="9" rx="3.2" ry="7.5"/><path d="M1.5 9h15"/>',
    "doc": '<path d="M4 1.5h6.5L14.5 5.5v10a1 1 0 0 1-1 1h-9.5a1 1 0 0 1-1-1v-13a1 1 0 0 1 1-1Z"/>'
           '<path d="M10.5 1.5v4h4"/><path d="M6 10h6.5M6 13h4.5"/>',
    "mail": '<rect x="1.5" y="3" width="15" height="12" rx="2"/><path d="m2 4.5 7 5.5 7-5.5"/>',
    "pen": '<path d="M3 15 4 11 12 3l3 3-8 8Z"/><path d="m10.5 4.5 3 3"/>',
}


def build_buttons() -> None:
    h = 44
    for file, label, icon, col in BUTTONS:
        a = C[col]
        w = int(16 + 18 + 10 + len(label) * 14 * SANS_W + 20)
        defs = card_defs(w, h, 12, "b")
        b = [card_open(w, h, 12, "b")]
        if icon == "linkedin":
            b.append(f'<rect x="16" y="13" width="18" height="18" rx="4" fill="{a}"/>'
                     f'<text x="19.6" y="27" class="sans" font-size="12" font-weight="800" fill="{C["card"]}">in</text>')
        else:
            b.append(f'<g transform="translate(16 13)" stroke="{a}" stroke-width="1.6" stroke-linecap="round" '
                     f'stroke-linejoin="round">{BTN_ICONS[icon]}</g>')
        b.append(f'<text x="44" y="27" class="sans" font-size="14" font-weight="600" fill="{C["text"]}">{esc(label)}</text>')
        b.append(card_close(w, h, 12, "b"))
        write(f"buttons/{file}.svg", svg(w, h, "\n".join(b), defs=defs, title=label))


# ───────────────────────────── FOOTER ───────────────────────────────────
def wave(amp: float, length: float, base: float, total: float = 1800) -> str:
    d = f"M0 {base}"
    x = 0.0
    while x < total:
        d += f"Q{x + length / 4:.0f} {base - amp} {x + length / 2:.0f} {base}T{x + length:.0f} {base}"
        x += length
    return d + f"V240H0Z"


def build_footer() -> None:
    w, h = W, 230
    defs = card_defs(w, h, 20, "ft") + f"""
<linearGradient id="cta" x1="230" y1="0" x2="670" y2="0" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="{C['lilac']}"/><stop offset=".5" stop-color="#fff"/>
  <stop offset="1" stop-color="{C['sky']}"/></linearGradient>
<linearGradient id="w1" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C['violet']}"/>
  <stop offset="1" stop-color="{C['cyan']}"/></linearGradient>"""
    css = """.w1{animation:w1 9s linear infinite}.w2{animation:w2 13s linear infinite}
@keyframes w1{to{transform:translateX(-300px)}}@keyframes w2{from{transform:translateX(-450px)}to{transform:translateX(0)}}"""
    b = [card_open(w, h, 20, "ft")]
    b.append(f'<path class="w2" d="{wave(9, 450, 196)}" fill="url(#w1)" opacity=".16"/>')
    b.append(f'<path class="w1" d="{wave(7, 300, 206)}" fill="url(#w1)" opacity=".28"/>')
    b.append(f'<text x="{w / 2}" y="70" text-anchor="middle" class="mono" font-size="11" letter-spacing="2.4" '
             f'fill="{C["violet"]}">06<tspan fill="{C["mute"]}"> / </tspan>CONTACT</text>')
    b.append(f'<text x="{w / 2}" y="110" text-anchor="middle" class="sans" font-size="30" font-weight="800" '
             f'letter-spacing="-.6" fill="url(#cta)">Let’s build something remarkable.</text>')
    b.append(f'<text x="{w / 2}" y="140" text-anchor="middle" class="sans" font-size="15" fill="{C["sub"]}">'
             f'Open to collaborations, consulting &amp; senior engineering roles.</text>')
    b.append(f'<text x="{w / 2}" y="170" text-anchor="middle" class="mono" font-size="13" fill="{C["cyan"]}">'
             f'→ {esc(EMAIL)}</text>')
    b.append(card_close(w, h, 20, "ft"))
    write("footer.svg", svg(w, h, "\n".join(b), css=css, defs=defs,
                            title=f"Let's build something remarkable — {EMAIL}"))


if __name__ == "__main__":
    print("Building static assets…")
    build_hero()
    build_about()
    build_focus()
    build_stack()
    build_work()
    build_buttons()
    build_footer()
    print("Done.")
