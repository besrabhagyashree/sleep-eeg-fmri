"""Study 01 README banner (light + dark SVG): the same 4 seconds of EEG in all four arms.

Real data: participant 1, sleep run 1, electrode O1, a light-sleep (N2) epoch. Each strip has its own
amplitude scale, printed beside it and chosen to fit the trace without clipping.

Usage: python src/postprocessing/study01_banner.py
Needs: data/raw/sub-01/eeg/sub-01_task-sleep_run-1_eeg.vhdr and data/clean/sub-01_task-sleep_run-1_clean-{mne,refined}_raw.fif
Writes: studies/01-preprocessing-ablation/assets/banner-{light,dark}.svg
"""
from pathlib import Path

import mne
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "studies" / "01-preprocessing-ablation" / "assets"
W, H = 1200, 360
X0, X1 = 640, 1150
T0, SECONDS, CH = 690.0, 4.0, "O1"
THEMES = {
    "light": dict(bg="#f5f6f9", panel="#ffffff", fg="#171926", muted="#5b5f72", rule="#e2e3ea",
                  arms=["#9a9cab", "#d97706", "#33318a", "#059669"], accent="#b53b6d"),
    "dark": dict(bg="#13141c", panel="#1a1c26", fg="#ebebf3", muted="#a3a6b8", rule="#2a2c3a",
                 arms=["#6d7085", "#f59e0b", "#aeabf5", "#34d399"], accent="#f28db6"),
}
LABELS = ["RAW · AS RECORDED", "FILTERED ONLY · 0.3–40 Hz", "CLEANED · MNE DETECTOR", "CLEANED · REFINED DETECTOR"]


def nice(v):
    for s in (50, 100, 150, 200, 300, 500, 1000, 1500, 2000, 2500, 3000, 5000):
        if v <= s:
            return s
    return float(np.ceil(v / 1000) * 1000)


def traces():
    raw = mne.io.read_raw_brainvision(ROOT / "data/raw/sub-01/eeg/sub-01_task-sleep_run-1_eeg.vhdr", preload=True, verbose="error")
    sf = raw.info["sfreq"]
    v0 = [a["onset"] for a in raw.annotations if a["description"].endswith("R128")][0]
    a = int((v0 + T0) * sf)
    r = raw.get_data(picks=[CH], start=a, stop=a + int(SECONDS * sf))[0] * 1e6
    f = raw.copy().crop(v0 + T0 - 10, v0 + T0 + SECONDS + 10).filter(0.3, 40.0, verbose="error").resample(250, verbose="error")
    fx = f.get_data(picks=[CH])[0] * 1e6
    fx = fx[int(10 * 250): int((10 + SECONDS) * 250)]
    out = [("env", r - np.median(r)), ("line", fx - np.median(fx))]
    for tag in ("mne", "refined"):
        c = mne.io.read_raw_fif(ROOT / f"data/clean/sub-01_task-sleep_run-1_clean-{tag}_raw.fif", verbose="error")
        x = c.get_data(picks=[CH], start=int(T0 * 250), stop=int((T0 + SECONDS) * 250))[0] * 1e6
        out.append(("line", x - np.median(x)))
    return out


def svg(p, data):
    mono = "'IBM Plex Mono', Consolas, monospace"
    sans = "'Segoe UI', Helvetica, Arial, sans-serif"
    parts = []
    band, top = 68, 52
    for i, ((kind, x), label, col) in enumerate(zip(data, LABELS, p["arms"])):
        yc = top + 34 + i * band
        lim = nice(np.abs(x).max())
        half = 22
        if kind == "env":
            cols = np.array_split(x, X1 - X0)
            path = "".join(f"M{X0 + j} {yc - c.max() / lim * half:.1f}V{yc - c.min() / lim * half:.1f}" for j, c in enumerate(cols))
            parts.append(f'<path d="{path}" stroke="{col}" stroke-width="1" fill="none"/>')
        else:
            xs = np.linspace(X0, X1, len(x))
            path = "M" + " L".join(f"{u:.1f} {yc - v / lim * half:.1f}" for u, v in zip(xs, x))
            parts.append(f'<path d="{path}" stroke="{col}" stroke-width="1.5" fill="none" stroke-linejoin="round"/>')
        parts.append(f'<text x="{X0}" y="{yc - 26}" font-family="{mono}" font-size="11" letter-spacing="1.2" fill="{col}">{label}</text>')
        parts.append(f'<text x="{X1}" y="{yc - 26}" text-anchor="end" font-family="{mono}" font-size="11" fill="{p["muted"]}">±{lim:,.0f} µV</text>')
    one_s = (X1 - X0) / SECONDS
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Study 01: the same EEG in four preprocessing arms">
  <defs><clipPath id="r"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>
  <g clip-path="url(#r)">
    <rect width="{W}" height="{H}" fill="{p["bg"]}"/>
    <rect x="0" y="0" width="8" height="{H}" fill="{p["arms"][2]}"/>
    <text x="56" y="86" font-family="{mono}" font-size="15" letter-spacing="3" fill="{p["accent"]}">STUDY 01 · ABLATION</text>
    <text x="54" y="152" font-family="Georgia, 'Times New Roman', serif" font-size="54" fill="{p["fg"]}">Does preprocessing</text>
    <text x="54" y="212" font-family="Georgia, 'Times New Roman', serif" font-size="54" fill="{p["fg"]}">matter?</text>
    <text x="56" y="256" font-family="Georgia, serif" font-style="italic" font-size="20" fill="{p["muted"]}">One sleep-staging classifier, four versions</text>
    <text x="56" y="282" font-family="Georgia, serif" font-style="italic" font-size="20" fill="{p["muted"]}">of the same in-scanner EEG, 33 people.</text>
    <rect x="{X0 - 24}" y="30" width="{X1 - X0 + 48}" height="{H - 50}" rx="14" fill="{p["panel"]}" stroke="{p["rule"]}"/>
    {"".join(parts)}
    <rect x="{X1 - one_s:.1f}" y="{H - 34}" width="{one_s:.1f}" height="3" fill="{p["fg"]}"/>
    <text x="{X1 - one_s - 8:.1f}" y="{H - 29}" text-anchor="end" font-family="{sans}" font-size="11.5" fill="{p["muted"]}">1 s</text>
    <text x="{X0}" y="{H - 29}" font-family="{sans}" font-size="11.5" fill="{p["muted"]}">Electrode O1 · light sleep (N2) · participant 1 · same 4 s</text>
  </g>
</svg>
'''


def main():
    data = traces()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, p in THEMES.items():
        (OUT / f"banner-{name}.svg").write_text(svg(p, data), encoding="utf-8")
    print("scales (uV):", [round(float(np.abs(x).max())) for _, x in data])


if __name__ == "__main__":
    main()
