"""Study 04 README banner (light + dark SVG) drawn from real data: one NIH night of expert sleep scoring.

Uses only the dataset's own labels (inventoried before registration); no EEG, feature or model output.

Usage: python studies/04-multisite-replication/make_banner.py
Needs: data/external/ds005127/derivatives/sleep_scoring_mr/sub-00067/ses-1/*.txt
Writes: studies/04-multisite-replication/assets/banner-light.svg, banner-dark.svg
"""
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCORES = ROOT / "data/external/ds005127/derivatives/sleep_scoring_mr/sub-00067/ses-1"
CODE = {(6, 0): "W", (4, 0): "N1", (3, 0): "N2", (2, 0): "N3", (1, 0): "N3", (4, 1): "R", (0, 0): None}
LEVELS = ["W", "R", "N1", "N2", "N3"]              # top to bottom, the usual hypnogram order
W, H = 1200, 360
PX0, PX1, PY0, PY1 = 676, 1150, 104, 226           # plot area
MONO = "'IBM Plex Mono', Consolas, monospace"
SANS = "'Segoe UI', Helvetica, Arial, sans-serif"

THEMES = {
    "light": dict(bg="#f5f6f9", panel="#ffffff", fg="#171926", muted="#5b5f72", rule="#e2e3ea",
                  hema="#33318a", eosin="#b53b6d", green="#059669", amber="#d97706", chip="#f1f2f6"),
    "dark": dict(bg="#13141c", panel="#1a1c26", fg="#ebebf3", muted="#a3a6b8", rule="#2a2c3a",
                 hema="#aeabf5", eosin="#f28db6", green="#34d399", amber="#f59e0b", chip="#222431"),
}


def night():
    """One segment per scanner run: list of (start datetime, [stage per 30-s epoch])."""
    runs = []
    for f in sorted(SCORES.glob("*.txt")):
        start = datetime.strptime(f.stem.split("acq-")[1], "%Y%m%dT%H%M")
        d = pd.read_csv(f, sep="\t")
        runs.append((start, [CODE.get((int(s), int(r))) for s, r in zip(d.Score, d.REM)]))
    return runs


def svg(p, runs):
    t0 = runs[0][0].replace(minute=0) + timedelta(minutes=30)       # 22:30
    t1 = t0 + timedelta(hours=6, minutes=30)                         # 05:00
    span = (t1 - t0).total_seconds()
    x = lambda t: PX0 + (t - t0).total_seconds() / span * (PX1 - PX0)
    y = lambda s: PY0 + LEVELS.index(s) * (PY1 - PY0) / (len(LEVELS) - 1)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="Study 04: does it replicate? One night of expert sleep scoring from the NIH dataset">',
         f'<defs><clipPath id="r"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs><g clip-path="url(#r)">',
         f'<rect width="{W}" height="{H}" fill="{p["bg"]}"/>',
         f'<rect x="0" y="0" width="8" height="{H}" fill="{p["hema"]}"/>',
         f'<text x="56" y="86" font-family="{MONO}" font-size="15" letter-spacing="3" fill="{p["eosin"]}">'
         f'STUDY 04 · REPLICATION</text>',
         f'<text x="54" y="152" font-family="Georgia, \'Times New Roman\', serif" font-size="54" fill="{p["fg"]}">'
         f'Does it replicate?</text>',
         f'<text x="56" y="200" font-family="Georgia, serif" font-style="italic" font-size="20" fill="{p["muted"]}">'
         f'Study 01\'s question, asked again in</text>',
         f'<text x="56" y="226" font-family="Georgia, serif" font-style="italic" font-size="20" fill="{p["muted"]}">'
         f'independent EEG-fMRI from two more sites.</text>']
    chips = [("PENN STATE", "29 · rest + sleep", p["hema"]), ("NIH", "16 · overnight", p["eosin"]),
             ("GENEVA", "18 · naps", p["green"])]
    cx = 56
    for name, sub, col in chips:
        w = 16 + 7.4 * max(len(name), len(sub))
        o += [f'<rect x="{cx}" y="262" width="{w:.0f}" height="50" rx="9" fill="{p["chip"]}" stroke="{p["rule"]}"/>',
              f'<rect x="{cx}" y="262" width="4" height="50" rx="2" fill="{col}"/>',
              f'<text x="{cx + 14}" y="282" font-family="{MONO}" font-size="11" letter-spacing="1.4" '
              f'fill="{col}">{name}</text>',
              f'<text x="{cx + 14}" y="302" font-family="{SANS}" font-size="12.5" fill="{p["fg"]}">{sub}</text>']
        cx += w + 12

    o += [f'<rect x="616" y="30" width="558" height="310" rx="14" fill="{p["panel"]}" stroke="{p["rule"]}"/>',
          f'<text x="640" y="66" font-family="{MONO}" font-size="11" letter-spacing="1.2" fill="{p["eosin"]}">'
          f'NIH · SUB-00067 · ONE NIGHT IN THE SCANNER</text>',
          f'<text x="1150" y="66" text-anchor="end" font-family="{MONO}" font-size="11" fill="{p["muted"]}">'
          f'expert scoring</text>']
    for s in LEVELS:
        o += [f'<line x1="{PX0}" x2="{PX1}" y1="{y(s):.1f}" y2="{y(s):.1f}" stroke="{p["rule"]}" stroke-width="1"/>',
              f'<text x="{PX0 - 12}" y="{y(s) + 4:.1f}" text-anchor="end" font-family="{MONO}" font-size="11" '
              f'fill="{p["muted"]}">{"REM" if s == "R" else s}</text>']
    for start, stages in runs:                     # scanner runs: shaded band, step line, REM highlighted
        a, b = x(start), x(start + timedelta(seconds=30 * len(stages)))
        o.append(f'<rect x="{a:.1f}" y="{PY0 - 10}" width="{b - a:.1f}" height="{PY1 - PY0 + 20}" rx="3" '
                 f'fill="{p["hema"]}" fill-opacity="0.07"/>')
        pts, prev = [], None
        for k, s in enumerate(stages):
            xa, xb = x(start + timedelta(seconds=30 * k)), x(start + timedelta(seconds=30 * (k + 1)))
            if s is None:
                if pts:
                    o.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{p["hema"]}" '
                             f'stroke-width="1.6" stroke-linejoin="round"/>')
                pts, prev = [], None
                continue
            if prev is not None and prev != s:
                pts.append(f"{xa:.1f},{y(s):.1f}")
            pts += [f"{xa:.1f},{y(s):.1f}", f"{xb:.1f},{y(s):.1f}"]
            if s == "R":
                o.append(f'<rect x="{xa:.1f}" y="{y(s) - 3:.1f}" width="{xb - xa:.1f}" height="6" '
                         f'fill="{p["eosin"]}"/>')
            prev = s
        if pts:
            o.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{p["hema"]}" stroke-width="1.6" '
                     f'stroke-linejoin="round"/>')
    t = t0 + timedelta(minutes=30)
    while t <= t1:
        o += [f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{PY1 + 12}" y2="{PY1 + 17}" stroke="{p["muted"]}"/>',
              f'<text x="{x(t):.1f}" y="{PY1 + 32}" text-anchor="middle" font-family="{MONO}" font-size="11" '
              f'fill="{p["muted"]}">{t:%H:%M}</text>']
        t += timedelta(hours=1)
    n = sum(len(s) for _, s in runs)
    o += [f'<rect x="640" y="288" width="14" height="10" rx="2" fill="{p["hema"]}" fill-opacity="0.12"/>',
          f'<text x="660" y="297" font-family="{SANS}" font-size="11.5" fill="{p["muted"]}">scanner run '
          f'({len(runs)} this night)</text>',
          f'<rect x="830" y="290" width="14" height="6" fill="{p["eosin"]}"/>',
          f'<text x="850" y="297" font-family="{SANS}" font-size="11.5" fill="{p["muted"]}">REM</text>',
          f'<text x="640" y="322" font-family="{SANS}" font-size="11.5" fill="{p["muted"]}">'
          f'{n} expert-scored 30-s epochs · gaps are breaks between scans · labels only, no results</text>',
          '</g></svg>']
    return "\n".join(o)


def main():
    runs = night()
    out = HERE / "assets"
    out.mkdir(exist_ok=True)
    for name, p in THEMES.items():
        (out / f"banner-{name}.svg").write_text(svg(p, runs), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
