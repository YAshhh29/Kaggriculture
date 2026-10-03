"""Build the README figures (SVG) from the numbers recorded in the project journal.

    python docs/assets/make_figures.py

Writes banner.svg, timeline.svg, architecture.svg and results.svg next to this
file. Every chart follows one palette (validated for colour-vision deficiency)
and switches to dark-mode colours when the viewer's system is in dark mode.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

# Chart chrome and the categorical palette (light / dark), in fixed slot order.
STYLE = f"""
  <style>
    .viz {{ font-family: {FONT}; }}
    .surface {{ fill: #fcfcfb; }}
    .ink {{ fill: #0b0b0b; }}
    .ink2 {{ fill: #52514e; }}
    .muted {{ fill: #898781; }}
    .grid {{ stroke: #e1e0d9; stroke-width: 1; }}
    .axis {{ stroke: #c3c2b7; stroke-width: 1; }}
    .ring {{ stroke: rgba(11,11,11,0.10); stroke-width: 1; fill: none; }}
    .s1 {{ fill: #2a78d6; }} .s2 {{ fill: #eb6834; }} .s3 {{ fill: #1baf7a; }} .s4 {{ fill: #eda100; }}
    .t1 {{ fill: #e8f1fc; }} .t2 {{ fill: #fdeee7; }} .t3 {{ fill: #e6f6f0; }} .t4 {{ fill: #fdf3dc; }}
    .ctx {{ fill: #c3c2b7; }}
    .panel {{ fill: #f3f2ee; }}
    .arrow {{ stroke: #898781; stroke-width: 2; fill: none; }}
    .arrowhead {{ fill: #898781; }}
    .gold {{ fill: #b07d10; }}
    @media (prefers-color-scheme: dark) {{
      .surface {{ fill: #1a1a19; }}
      .ink {{ fill: #ffffff; }}
      .ink2 {{ fill: #c3c2b7; }}
      .grid {{ stroke: #2c2c2a; }}
      .axis {{ stroke: #383835; }}
      .ring {{ stroke: rgba(255,255,255,0.10); }}
      .s1 {{ fill: #3987e5; }} .s2 {{ fill: #d95926; }} .s3 {{ fill: #199e70; }} .s4 {{ fill: #c98500; }}
      .t1 {{ fill: #1c2a3c; }} .t2 {{ fill: #3a241b; }} .t3 {{ fill: #17302a; }} .t4 {{ fill: #352c17; }}
      .ctx {{ fill: #5d5c58; }}
      .panel {{ fill: #242423; }}
      .gold {{ fill: #e0b04a; }}
    }}
  </style>"""


def svg(width: int, height: int, body: str, title: str, desc: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d" class="viz">\n'
            f'  <title id="t">{escape(title)}</title>\n  <desc id="d">{escape(desc)}</desc>\n'
            f'{STYLE}\n  <rect class="surface" x="0" y="0" width="{width}" height="{height}" rx="12"/>\n'
            f'  <rect class="ring" x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12"/>\n'
            f'{body}\n</svg>\n')


def text(x, y, s, cls="ink", size=14, weight=400, anchor="start", extra=""):
    return (f'  <text x="{x}" y="{y}" class="{cls}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{extra}>{escape(s)}</text>\n')


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
def banner() -> str:
    w, h = 1280, 320
    rows = []
    # field rows on the lower half, drawn in perspective-free stripes
    for i in range(7):
        y = 236 + i * 13
        rows.append(f'  <rect x="0" y="{y}" width="{w}" height="8" fill="#6b8f3a" opacity="{0.55 + i * 0.06:.2f}"/>\n')
    wheat = []
    for i in range(26):
        x = 40 + i * 48
        if 940 <= x <= 1110:      # leave the barn clear
            continue
        wheat.append(f'  <g transform="translate({x},230)" stroke="#d9b44a" stroke-width="3" stroke-linecap="round">'
                     f'<line x1="0" y1="0" x2="0" y2="-34"/><line x1="0" y1="-20" x2="-8" y2="-28"/>'
                     f'<line x1="0" y1="-20" x2="8" y2="-28"/><line x1="0" y1="-10" x2="-8" y2="-18"/>'
                     f'<line x1="0" y1="-10" x2="8" y2="-18"/></g>\n')
    body = f"""
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#16324f"/><stop offset="1" stop-color="#2f6f73"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="{w}" height="{h}" rx="12" fill="url(#sky)"/>
  <circle cx="1130" cy="78" r="42" fill="#f4c95d" opacity="0.95"/>
  <circle cx="1130" cy="78" r="62" fill="#f4c95d" opacity="0.15"/>
  <g transform="translate(980,134)">
    <rect x="0" y="34" width="96" height="62" fill="#b5442f"/>
    <polygon points="-8,36 48,0 104,36" fill="#8f3324"/>
    <rect x="36" y="58" width="24" height="38" fill="#f1e3c4"/>
    <line x1="36" y1="58" x2="60" y2="96" stroke="#b5442f" stroke-width="3"/>
    <line x1="60" y1="58" x2="36" y2="96" stroke="#b5442f" stroke-width="3"/>
  </g>
  <rect x="0" y="230" width="{w}" height="{h - 230}" fill="#3f5f24"/>
{''.join(rows)}{''.join(wheat)}
  <text x="56" y="96" fill="#ffffff" font-size="58" font-weight="700" font-family="{FONT}">Kaggriculture</text>
  <text x="58" y="136" fill="#d7e6e4" font-size="22" font-family="{FONT}">An AI that runs a farm, a crew and a market stall for 30 days — and races a rival to the bank</text>
  <g transform="translate(58,154)">
    <rect x="0" y="0" width="356" height="34" rx="17" fill="#ffffff" opacity="0.14"/>
    <circle cx="20" cy="17" r="9" fill="#c9ced6"/><circle cx="20" cy="17" r="5" fill="#9aa3ad"/>
    <text x="38" y="23" fill="#ffffff" font-size="16" font-weight="600" font-family="{FONT}">Silver medal · 448th of 10,246 teams</text>
  </g>
"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="t d">\n  <title id="t">Kaggriculture</title>\n'
            f'  <desc id="d">Project banner: Kaggriculture, silver medal, 448th of 10,246 teams.</desc>\n'
            f'{body}</svg>\n')


# ---------------------------------------------------------------------------
# Timeline: five phases, drawn as equal cards (not to scale; dates on each)
# ---------------------------------------------------------------------------
PHASES = [
    ("Aug 17 – 30", "Foundations", 1,
     ["Simulator, rulebook, a deterministic", "wheat baseline", "~90 experimental agents and", "learned selectors"]),
    ("Aug 31 – Sep 8", "Candidates A–F", 2,
     ["Residual-RL contracts", "Clones of elite players' routes,", "route search over 245 tapes", "An economics engine (E)"]),
    ("Sep 9 – 25", "Candidates G–K", 3,
     ["A farm built from the rules (G)", "Market-demand layer (H, H2)", "Coins-per-worker scheduler (J)", "Benchmarks that flattered us, fixed"]),
    ("Sep 26 – 27", "L and M", 4,
     ["Layer stack on a public clone", "Shadow of 18 public programs", "In-game rival sell clock (M)", "Peak live rating 2,492 (L3)"]),
    ("Sep 28 – 30", "N1 → N12", 1,
     ["Stack moved to the best public plan", "Tomato annex, slot races, guards", "Shed guard: +9 wins, 0 losses (N10)", "Final pair: N11 + N10"]),
]


def timeline() -> str:
    w, h = 1280, 330
    cw, gap, x0, y0 = 232, 14, 24, 74
    body = [text(24, 40, "From a wheat baseline to a silver medal in six weeks", size=20, weight=700),
            text(24, 62, "502 commits, five phases — each card is one phase (cards are not drawn to time scale)",
                 cls="ink2", size=14)]
    for i, (dates, name, slot, bullets) in enumerate(PHASES):
        x = x0 + i * (cw + gap)
        body.append(f'  <rect class="t{slot}" x="{x}" y="{y0}" width="{cw}" height="200" rx="10"/>\n')
        body.append(f'  <rect class="s{slot}" x="{x}" y="{y0}" width="{cw}" height="6" rx="3"/>\n')
        body.append(text(x + 16, y0 + 32, dates, cls="ink2", size=13, weight=600))
        body.append(text(x + 16, y0 + 58, name, size=20, weight=700))
        for j, b in enumerate(bullets):
            body.append(text(x + 16, y0 + 90 + j * 24, b, cls="ink2", size=13))
        if i < len(PHASES) - 1:
            ax = x + cw + 1
            body.append(f'  <path class="arrowhead" d="M{ax} {y0 + 92} l{gap - 3} 8 l-{gap - 3} 8 z"/>\n')
    # finish line
    body.append(f'  <rect class="panel" x="24" y="290" width="{w - 48}" height="28" rx="14"/>\n')
    body.append(text(w / 2, 309, "Deadline 30 Sep 23:59 UTC  ·  final pair N11 + N10  ·  "
                     "448th of 10,246 teams  ·  silver medal", cls="ink", size=14, weight=600, anchor="middle"))
    return svg(w, h, "".join(body), "Project timeline",
               "Five phases from 17 August to 30 September 2026: foundations, candidates A to F, candidates G to K, "
               "agents L and M, and the N series that produced the final pair N11 and N10.")


# ---------------------------------------------------------------------------
# Architecture of the final agent (N11), outermost layer at the top
# ---------------------------------------------------------------------------
KIND = {1: "Market", 2: "Guard", 3: "Farm", 4: "Opponent model"}
LAYERS = [  # (file, introduced in, kind slot, what it does)
    ("safety", "L", 2, "Never crashes: repairs malformed actions and keeps a 60-second time budget"),
    ("own_book", "N11", 4, "Tells the parent what we really sold, so it stops reading our sales as the rival's"),
    ("shed_guard", "N10", 2, "Sells or cancels purchases so the day-end shed overflow destroys nothing"),
    ("place_guard", "N7", 2, "Builds the pen first when an animal is about to be placed on bare ground"),
    ("draw_last", "N4", 1, "Orders the town-draw wheat purchase around riders who copy it"),
    ("tomato_annex", "N3", 3, "Plants a gated five-tile tomato annex when the town is short of tomatoes"),
    ("m_sell", "M", 4, "Learns the rival's selling clock during the game and sells just before it"),
    ("l2_shadow", "L3", 4, "Runs 18 public programs in lockstep; when one matches the rival, front-runs its sales"),
    ("l2_labour", "L2", 3, "Gives idle hands useful work on the tile they are already standing on"),
    ("market_front", "L", 1, "Puts the orders with the most price damage into the earliest market slots"),
    ("l2_outfarm (lot)", "L2", 1, "Sells a whole lot at once when racing the rival for the same product"),
    ("l2_wheat_rt", "L2", 1, "Buys wheat just before the town eats it and sells it back a turn later"),
    ("l2_animals", "L2", 3, "Drops feeds that provably earn nothing"),
]


def architecture() -> str:
    w = 1280
    x0, bw, bh, gap, top = 150, 1010, 40, 6, 112
    n = len(LAYERS)
    parent_y = top + n * (bh + gap) + 8
    h = parent_y + 118
    body = [text(24, 40, "How the final agent (N11) decides each turn", size=20, weight=700),
            text(24, 62, "Each layer wraps the one below it: the observation travels down, "
                         "the parent proposes an action, and every layer may adjust it on the way back up",
                 cls="ink2", size=14)]
    # legend
    lx = 24
    for slot in (1, 2, 3, 4):
        body.append(f'  <rect class="s{slot}" x="{lx}" y="78" width="14" height="14" rx="3"/>\n')
        body.append(text(lx + 20, 90, KIND[slot], cls="ink2", size=13))
        lx += 34 + len(KIND[slot]) * 8
    # flow arrows
    ay1, ay2 = top + 4, parent_y + 40
    body.append(f'  <path class="arrow" d="M80 {ay1} V{ay2}"/>\n'
                f'  <path class="arrowhead" d="M72 {ay2 - 2} l8 14 l8 -14 z"/>\n')
    body.append(text(68, (ay1 + ay2) / 2, "observation in", cls="muted", size=13, anchor="middle",
                     extra=f' transform="rotate(-90 68 {(ay1 + ay2) / 2})"'))
    rx = x0 + bw + 50
    body.append(f'  <path class="arrow" d="M{rx} {ay2} V{ay1 + 10}"/>\n'
                f'  <path class="arrowhead" d="M{rx - 8} {ay1 + 12} l8 -14 l8 14 z"/>\n')
    body.append(text(rx + 18, (ay1 + ay2) / 2, "action out", cls="muted", size=13, anchor="middle",
                     extra=f' transform="rotate(90 {rx + 18} {(ay1 + ay2) / 2})"'))
    for i, (name, intro, slot, what) in enumerate(LAYERS):
        y = top + i * (bh + gap)
        body.append(f'  <rect class="t{slot}" x="{x0}" y="{y}" width="{bw}" height="{bh}" rx="8"/>\n')
        body.append(f'  <rect class="s{slot}" x="{x0}" y="{y}" width="6" height="{bh}" rx="3"/>\n')
        body.append(text(x0 + 20, y + 26, name, size=15, weight=700))
        body.append(text(x0 + 200, y + 26, what, cls="ink2", size=14))
        body.append(text(x0 + bw - 14, y + 26, intro, cls="muted", size=13, weight=600, anchor="end"))
    body.append(f'  <rect class="panel" x="{x0}" y="{parent_y}" width="{bw}" height="96" rx="10"/>\n')
    body.append(f'  <rect class="ring" x="{x0 + 0.5}" y="{parent_y + 0.5}" width="{bw - 1}" height="95" rx="10" '
                f'stroke-dasharray="6 5"/>\n')
    body.append(text(x0 + 20, parent_y + 32, "Parent: the 2965 Master Hybrid Engine", size=16, weight=700))
    body.append(text(x0 + 20, parent_y + 56, "A public Kaggle notebook (Apache-2.0). It follows one of 41 recorded "
                     "30-day routes, chosen on day 6 from the town's first two shops,", cls="ink2", size=14))
    body.append(text(x0 + 20, parent_y + 78, "and switches to a shared end-game route on day 27. "
                     "Our 13 layers sit on top; its own code is unchanged except one patch (wool first).",
                     cls="ink2", size=14))
    return svg(w, h, "".join(body), "Architecture of the final agent",
               "Thirteen layers wrap a public route-following parent: four guards, four market layers, "
               "three farm layers and three opponent-modelling layers, outermost first.")


# ---------------------------------------------------------------------------
# Results: every candidate on the final day's real ladder games
# ---------------------------------------------------------------------------
RESULTS = [  # (agent, note, won, played, submitted in the final pair)
    ("N11", "final pair", 133, 205, True),
    ("N12", "N11 + newest library", 133, 205, False),
    ("N10", "final pair", 131, 205, True),
    ("N8", "29 Sep", 123, 202, False),
    ("N9", "30 Sep morning", 123, 205, False),
    ("H2", "9 Sep", 32, 191, False),
    ("C2", "3 Sep", 11, 191, False),
]


def results() -> str:
    w = 1280
    lx, bx, bw, rh, top = 24, 300, 780, 40, 112
    h = top + len(RESULTS) * rh + 48
    body = [text(24, 40, "Win rate on the last day's real ladder games", size=20, weight=700),
            text(24, 62, "Every candidate replayed move for move against the opponents N9 and N10 actually met on "
                         "30 September (205 games; same towns, same opponent moves)", cls="ink2", size=14)]
    body.append(f'  <rect class="s1" x="24" y="78" width="14" height="14" rx="3"/>\n')
    body.append(text(44, 90, "Submitted (final pair)", cls="ink2", size=13))
    body.append(f'  <rect class="ctx" x="214" y="78" width="14" height="14" rx="3"/>\n')
    body.append(text(234, 90, "Other candidates", cls="ink2", size=13))
    base = top + len(RESULTS) * rh
    for pct in (0, 25, 50, 75, 100):
        x = bx + bw * pct / 100
        body.append(f'  <line class="{"axis" if pct == 0 else "grid"}" x1="{x}" y1="{top - 6}" x2="{x}" y2="{base}"/>\n')
        body.append(text(x, base + 20, f"{pct}%", cls="muted", size=12, anchor="middle"))
    for i, (name, note, won, played, final) in enumerate(RESULTS):
        y = top + i * rh
        pct = 100 * won / played
        body.append(text(lx, y + 25, name, size=16, weight=700))
        body.append(text(lx + 48, y + 25, note, cls="ink2", size=13))
        barw = max(2, bw * pct / 100)
        body.append(f'  <rect class="{"s1" if final else "ctx"}" x="{bx}" y="{y + 8}" width="{barw:.1f}" '
                    f'height="{rh - 16}" rx="4"/>\n')
        body.append(text(bx + barw + 10, y + 26, f"{pct:.1f}%", size=14, weight=700))
        body.append(text(bx + barw + 62, y + 26, f"{won} / {played}", cls="muted", size=13))
    return svg(w, h, "".join(body), "Win rate on the last day's real ladder games",
               "; ".join(f"{n} {100 * a / b:.1f}% ({a} of {b})" for n, _, a, b, _ in RESULTS))


if __name__ == "__main__":
    for name, build in (("banner", banner), ("timeline", timeline), ("architecture", architecture),
                        ("results", results)):
        (OUT / f"{name}.svg").write_text(build(), encoding="utf-8")
        print("wrote", OUT / f"{name}.svg")
