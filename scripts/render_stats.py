"""Render assets/stats.svg — an on-brand GitHub activity panel.

    python scripts/render_stats.py            # uses GH_TOKEN / GITHUB_TOKEN if set
    GH_USER=someone python scripts/render_stats.py

With a token it uses the GraphQL API (accurate languages, all-time calendar).
Without one it falls back to public pages + REST, which is good enough for a
first local render. Standard library only, so the Action needs no installs.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from design import C, W, card_close, card_defs, card_open, esc, eyebrow, svg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "stats.svg"
UA = {"User-Agent": "profile-stats-renderer"}

# Markup/templating languages inflate byte counts without saying much about skill.
EXCLUDE = {"HTML", "CSS", "SCSS", "Sass", "Less", "EJS", "Makefile", "Dockerfile",
           "Procfile", "Batchfile"}
ALIASES = {"Hack": "PHP"}  # Linguist often misreads PHP templates as Hack
LANG_COLORS = [C["violet"], C["cyan"], C["pink"], C["amber"], C["green"], C["lilac"], C["mute"]]
LEVELS = ["#16162A", "#2C2560", "#5A44C8", "#8B5CF6", "#38D3EE"]


@dataclass
class Stats:
    login: str
    created_year: int
    public_repos: int
    days: dict[date, int] = field(default_factory=dict)
    lang_bytes: Counter = field(default_factory=Counter)


# ─────────────────────────────── fetching ───────────────────────────────
def http(url: str, *, data: bytes | None = None, headers: dict | None = None, tries: int = 4) -> bytes:
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError):
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def gql(token: str, query: str, **variables) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    res = json.loads(http("https://api.github.com/graphql", data=body,
                          headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"}))
    if res.get("errors"):
        raise RuntimeError(res["errors"])
    return res["data"]


Q_USER = """query($login:String!,$after:String){user(login:$login){createdAt
 all:repositories(ownerAffiliations:OWNER,privacy:PUBLIC){totalCount}
 repositories(ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false,first:100,after:$after){
  pageInfo{hasNextPage endCursor}
  nodes{languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}"""

Q_CAL = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
 contributionsCollection(from:$from,to:$to){contributionCalendar{
  weeks{contributionDays{date contributionCount}}}}}}"""


def fetch_graphql(login: str, token: str) -> Stats:
    after, st = None, None
    while True:
        u = gql(token, Q_USER, login=login, after=after)["user"]
        if st is None:
            st = Stats(login, int(u["createdAt"][:4]), u["all"]["totalCount"])
        for repo in u["repositories"]["nodes"]:
            for e in repo["languages"]["edges"]:
                st.lang_bytes[e["node"]["name"]] += e["size"]
        page = u["repositories"]["pageInfo"]
        if not page["hasNextPage"]:
            break
        after = page["endCursor"]

    now = datetime.now(timezone.utc)
    for year in range(st.created_year, now.year + 1):
        to = min(datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc), now)
        cal = gql(token, Q_CAL, login=login,
                  **{"from": f"{year}-01-01T00:00:00Z", "to": to.strftime("%Y-%m-%dT%H:%M:%SZ")})
        for wk in cal["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in wk["contributionDays"]:
                st.days[date.fromisoformat(d["date"])] = d["contributionCount"]
    return st


def parse_calendar_html(html: str) -> dict[date, int]:
    ids = dict(re.findall(r'data-date="(\d{4}-\d\d-\d\d)" id="(contribution-day-component-\d+-\d+)"', html))
    by_id = {v: k for k, v in ids.items()}
    out: dict[date, int] = {}
    for cid, n in re.findall(r'for="(contribution-day-component-\d+-\d+)"[^>]*>(No|[\d,]+) contribution', html):
        if cid in by_id:
            out[date.fromisoformat(by_id[cid])] = 0 if n == "No" else int(n.replace(",", ""))
    return out


def fetch_public(login: str) -> Stats:
    user = json.loads(http(f"https://api.github.com/users/{login}"))
    repos, page = [], 1
    while True:
        batch = json.loads(http(f"https://api.github.com/users/{login}/repos?per_page=100&type=owner&page={page}"))
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    st = Stats(login, int(user["created_at"][:4]), user["public_repos"])
    for r in repos:  # approximation: primary language weighted by repo size
        if not r["fork"] and r["language"]:
            st.lang_bytes[r["language"]] += max(r["size"], 1) * 1024
    today = date.today()
    for year in range(st.created_year, today.year + 1):
        html = http(f"https://github.com/users/{login}/contributions?from={year}-01-01&to={year}-12-31").decode()
        st.days.update({d: n for d, n in parse_calendar_html(html).items() if d <= today})
    return st


# ─────────────────────────────── metrics ────────────────────────────────
def streaks(days: dict[date, int], today: date) -> tuple[int, int]:
    longest = run = 0
    for d in sorted(days):
        if d > today:
            break
        run = run + 1 if days[d] > 0 else 0
        longest = max(longest, run)
    cur, d = 0, today
    if days.get(d, 0) == 0:          # today not counted yet → start from yesterday
        d -= timedelta(days=1)
    while days.get(d, 0) > 0:
        cur += 1
        d -= timedelta(days=1)
    return longest, cur


def top_languages(lang_bytes: Counter, n: int = 6) -> list[tuple[str, float]]:
    merged: Counter = Counter()
    for k, v in lang_bytes.items():
        k = ALIASES.get(k, k)
        if k not in EXCLUDE:
            merged[k] += v
    total = sum(merged.values()) or 1
    top = merged.most_common(n)
    rest = total - sum(v for _, v in top)
    out = [(k, v / total * 100) for k, v in top]
    if rest / total > .005:
        out.append(("Other", rest / total * 100))
    return out


# ─────────────────────────────── render ─────────────────────────────────
def render(st: Stats, today: date | None = None) -> str:
    today = today or datetime.now(timezone.utc).date()
    w, h = W, 406
    longest, current = streaks(st.days, today)
    total = sum(v for d, v in st.days.items() if d <= today)
    start = today - timedelta(days=(today.weekday() + 1) % 7) - timedelta(weeks=52)  # a Sunday
    window = {start + timedelta(days=i): st.days.get(start + timedelta(days=i), 0)
              for i in range((today - start).days + 1)}
    year_total = sum(v for d, v in window.items() if d > today - timedelta(days=365))
    langs = top_languages(st.lang_bytes)

    defs = card_defs(w, h, 20, "st") + f"""
<linearGradient id="num" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff"/>
  <stop offset="1" stop-color="{C['lilac']}"/></linearGradient>
<linearGradient id="scan" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C['cyan']}" stop-opacity="0"/>
  <stop offset=".5" stop-color="{C['cyan']}" stop-opacity=".22"/><stop offset="1" stop-color="{C['cyan']}" stop-opacity="0"/></linearGradient>
<clipPath id="bar"><rect x="572" y="134" width="284" height="8" rx="4"/></clipPath>
<clipPath id="heat"><rect x="50" y="262" width="800" height="110"/></clipPath>"""
    css = """.scan{animation:scan 8s ease-in-out infinite}
@keyframes scan{0%{transform:translateX(-120px)}55%,100%{transform:translateX(900px)}}
.grow{transform-box:fill-box;transform-origin:left;animation:grow 1.1s cubic-bezier(.2,.7,.2,1) both .3s}
@keyframes grow{from{transform:scaleX(0)}}"""

    b = [card_open(w, h, 20, "st"), eyebrow(28, 40, "05", "ACTIVITY")]
    b.append(f'<text x="28" y="72" class="sans" font-size="21" font-weight="700" fill="{C["text"]}">GitHub at a glance</text>')
    b.append(f'<text x="{w - 28}" y="40" text-anchor="end" class="mono" font-size="10" letter-spacing="1.6" '
             f'fill="{C["mute"]}">AUTO-UPDATED · {today.isoformat()}</text>')

    n_langs = len({ALIASES.get(k, k) for k in st.lang_bytes} - EXCLUDE)
    # Current streak is computed but deliberately not shown: a "0 days" tile
    # reads badly on a profile even when the work is happening in private repos.
    _ = current
    tiles = [(f"{total:,}", "", "ALL-TIME CONTRIBUTIONS"), (f"{year_total:,}", "", "PAST 12 MONTHS"),
             (f"{st.public_repos:,}", "", "PUBLIC REPOSITORIES"),
             (f"{n_langs}", "", "LANGUAGES WRITTEN"),
             (f"{longest:,}", " days" if longest != 1 else " day", "LONGEST STREAK"),
             (str(st.created_year), "", "BUILDING ON GITHUB SINCE")]
    for i, (val, unit, label) in enumerate(tiles):
        x, y = 28 + (i % 3) * 172, 96 + (i // 3) * 72
        b.append(f'<g class="in" style="animation-delay:{.1 + i * .08:.2f}s">'
                 f'<rect x="{x}" y="{y}" width="162" height="62" rx="12" fill="{C["card2"]}" stroke="{C["line"]}"/>'
                 f'<text x="{x + 16}" y="{y + 31}" class="sans" font-size="23" font-weight="800" fill="url(#num)">'
                 f'{esc(val)}<tspan font-size="13" font-weight="600" fill="{C["sub"]}">{esc(unit)}</tspan></text>'
                 f'<text x="{x + 16}" y="{y + 49}" class="mono" font-size="9" letter-spacing="1.3" '
                 f'fill="{C["mute"]}">{esc(label)}</text></g>')

    # Languages
    b.append(f'<g class="in" style="animation-delay:.3s">'
             f'<rect x="556" y="96" width="316" height="134" rx="12" fill="{C["card2"]}" stroke="{C["line"]}"/>'
             f'<text x="572" y="121" class="mono" font-size="9.5" letter-spacing="1.5" fill="{C["mute"]}">TOP LANGUAGES</text>'
             f'<g clip-path="url(#bar)"><g class="grow"><rect x="572" y="134" width="284" height="8" fill="{C["line"]}"/>')
    x = 572.0
    for i, (_, pct) in enumerate(langs):
        lw = 284 * pct / 100
        b.append(f'<rect x="{x:.2f}" y="134" width="{lw + .6:.2f}" height="8" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
        x += lw
    b.append("</g></g>")
    for i, (name, pct) in enumerate(langs[:6]):
        lx, ly = 572 + (i % 2) * 146, 168 + (i // 2) * 22
        col = LANG_COLORS[i % len(LANG_COLORS)]
        b.append(f'<circle cx="{lx + 4}" cy="{ly - 4}" r="4" fill="{col}"/>'
                 f'<text x="{lx + 14}" y="{ly}" class="sans" font-size="12.5" fill="{C["text"]}">{esc(name)}</text>'
                 f'<text x="{lx + 134}" y="{ly}" text-anchor="end" class="mono" font-size="10.5" '
                 f'fill="{C["mute"]}">{pct:.1f}%</text>')
    b.append("</g>")

    # Heatmap
    nz = sorted(v for v in window.values() if v > 0)
    q = [nz[int(len(nz) * f)] if nz else 1 for f in (.25, .5, .75)]

    def level(v: int) -> int:
        return 0 if v <= 0 else 1 if v <= q[0] else 2 if v <= q[1] else 3 if v <= q[2] else 4

    x0, y0, cell, step = 54, 266, 12, 15
    last_month = None
    cols: dict[int, list[str]] = {}
    for d, v in window.items():
        c, r = (d - start).days // 7, (d - start).days % 7
        if r == 0 and d.month != last_month and c < 51:
            b.append(f'<text x="{x0 + c * step}" y="{y0 - 9}" class="mono" font-size="9.5" '
                     f'fill="{C["mute"]}">{d.strftime("%b")}</text>')
            last_month = d.month
        cols.setdefault(c, []).append(
            f'<rect x="{x0 + c * step}" y="{y0 + r * step}" width="{cell}" height="{cell}" rx="3" '
            f'fill="{LEVELS[level(v)]}"><title>{v} on {d.isoformat()}</title></rect>')
    for c, rects in cols.items():
        b.append(f'<g class="in" style="animation-delay:{.2 + c * .014:.3f}s">{"".join(rects)}</g>')
    b.append(f'<g clip-path="url(#heat)"><rect class="scan" x="0" y="262" width="120" height="110" fill="url(#scan)"/></g>')

    b.append(f'<text x="{x0}" y="392" class="mono" font-size="10.5" fill="{C["sub"]}">'
             f'{year_total:,} contributions in the last year</text>')
    lx = w - 54 - 5 * 15 - 34
    b.append(f'<text x="{lx - 8}" y="392" text-anchor="end" class="mono" font-size="9.5" fill="{C["mute"]}">Less</text>')
    for i, col in enumerate(LEVELS):
        b.append(f'<rect x="{lx + i * 15}" y="382" width="12" height="12" rx="3" fill="{col}"/>')
    b.append(f'<text x="{lx + 5 * 15 + 4}" y="392" class="mono" font-size="9.5" fill="{C["mute"]}">More</text>')

    b.append(card_close(w, h, 20, "st"))
    title = (f"GitHub activity for {st.login}: {total:,} contributions all-time, {year_total:,} in the past year, "
             f"longest streak {longest} days, top languages " + ", ".join(n for n, _ in langs[:4]))
    return svg(w, h, "\n".join(b), title=title, css=css, defs=defs)


def main() -> None:
    login = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "0xJarmenKell"
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    st = fetch_graphql(login, token) if token else fetch_public(login)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(st), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} for {login} ({'graphql' if token else 'public fallback'})")


if __name__ == "__main__":
    main()
