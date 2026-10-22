"""README banner (light + dark SVG) drawn from real data: raw vs cleaned EEG, participant 1.

Usage: python src/postprocessing/readme_banner.py
Needs: data/raw/sub-01/eeg/sub-01_task-sleep_run-1_eeg.vhdr and the matching cleaned file
       data/clean/sub-01_task-sleep_run-1_clean_raw.fif (from preprocessing/mr_artifacts.py).
Writes: assets/banner-light.svg, assets/banner-dark.svg
"""
from pathlib import Path

import mne
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
W, H = 1200, 320
PX0, PX1 = 724, 1136          # trace area (x)
T0, SECONDS, CH = 690.0, 4.0, "O1"   # an N2 epoch of sleep run 1 (seconds from the first scanner volume)

THEMES = {
    "light": dict(bg="#f5f6f9", panel="#ffffff", fg="#171926", muted="#5b5f72", rule="#e2e3ea",
                  hema="#33318a", eosin="#b53b6d", raw="#9a9cab"),
    "dark": dict(bg="#13141c", panel="#1a1c26", fg="#ebebf3", muted="#a3a6b8", rule="#2a2c3a",
                 hema="#aeabf5", eosin="#f28db6", raw="#6d7085"),
}


def raw_envelope(n_px):
    raw = mne.io.read_raw_brainvision(ROOT / "data/raw/sub-01/eeg/sub-01_task-sleep_run-1_eeg.vhdr",
                                      preload=False, verbose="error")
    sf = raw.info["sfreq"]
    first_vol = [a["onset"] for a in raw.annotations if a["description"].endswith("R128")][0]
    a = int((first_vol + T0) * sf)
    x = raw.get_data(picks=[CH], start=a, stop=a + int(SECONDS * sf))[0] * 1e6
    x -= np.median(x)
    cols = np.array_split(x, n_px)
    return np.array([c.min() for c in cols]), np.array([c.max() for c in cols])


def clean_trace():
    c = mne.io.read_raw_fif(ROOT / "data/clean/sub-01_task-sleep_run-1_clean_raw.fif", preload=False,
                            verbose="error")
    sf = c.info["sfreq"]
    x = c.get_data(picks=[CH], start=int(T0 * sf), stop=int((T0 + SECONDS) * sf))[0] * 1e6
    return x - np.median(x)


def svg(p, lo, hi, cl):
    n = len(lo)
    xs = np.linspace(PX0, PX1, n)
    yr, half_r, lim_r = 132, 38, 2300.0          # raw band: +-2300 uV -> +-38 px (no clipping)
    raw_path = "".join(f"M{x:.1f} {yr - np.clip(b, -lim_r, lim_r) / lim_r * half_r:.1f}"
                       f"V{yr - np.clip(t, -lim_r, lim_r) / lim_r * half_r:.1f}" for x, b, t in zip(xs, lo, hi))
    yc, half_c, lim_c = 246, 32, 120.0           # cleaned band: +-120 uV -> +-32 px (no clipping)
    xc = np.linspace(PX0, PX1, len(cl))
    yy = yc - np.clip(cl, -lim_c, lim_c) / lim_c * half_c
    clean_path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in zip(xc, yy))
    one_s = (PX1 - PX0) / SECONDS
    mono = "'IBM Plex Mono', Consolas, monospace"
    sans = "'Segoe UI', Helvetica, Arial, sans-serif"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Sleep EEG-fMRI: raw in-scanner EEG and the same EEG after cleaning">
  <defs><clipPath id="r"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>
  <g clip-path="url(#r)">
    <rect width="{W}" height="{H}" fill="{p["bg"]}"/>
    <rect x="0" y="0" width="8" height="{H}" fill="{p["hema"]}"/>
    <text x="56" y="80" font-family="{mono}" font-size="15" letter-spacing="3" fill="{p["eosin"]}">SLEEP · EEG · fMRI</text>
    <text x="54" y="152" font-family="Georgia, 'Times New Roman', serif" font-size="66" fill="{p["fg"]}">Sleep EEG-fMRI</text>
    <text x="56" y="196" font-family="Georgia, serif" font-style="italic" font-size="22" fill="{p["muted"]}">Brain activity recorded inside an MRI scanner,</text>
    <text x="56" y="224" font-family="Georgia, serif" font-style="italic" font-size="22" fill="{p["muted"]}">cleaned, measured and modelled.</text>
    <text x="56" y="272" font-family="{mono}" font-size="13.5" fill="{p["muted"]}">OpenNeuro ds003768 · 33 adults · 58 h of expert-scored sleep</text>
    <rect x="{PX0 - 24}" y="44" width="{PX1 - PX0 + 48}" height="262" rx="14" fill="{p["panel"]}" stroke="{p["rule"]}"/>
    <text x="{PX0}" y="76" font-family="{mono}" font-size="12" letter-spacing="1.5" fill="{p["muted"]}">RAW · AS RECORDED</text>
    <text x="{PX1}" y="76" text-anchor="end" font-family="{mono}" font-size="12" fill="{p["muted"]}">±2,300 µV</text>
    <path d="{raw_path}" stroke="{p["raw"]}" stroke-width="1" fill="none"/>
    <line x1="{PX0}" y1="182" x2="{PX1}" y2="182" stroke="{p["rule"]}" stroke-dasharray="3 4"/>
    <text x="{PX0}" y="202" font-family="{mono}" font-size="12" letter-spacing="1.5" fill="{p["hema"]}">CLEANED · SCANNER + HEARTBEAT REMOVED</text>
    <text x="{PX1}" y="202" text-anchor="end" font-family="{mono}" font-size="12" fill="{p["muted"]}">±120 µV</text>
    <path d="{clean_path}" stroke="{p["hema"]}" stroke-width="1.6" fill="none" stroke-linejoin="round"/>
    <rect x="{PX1 - one_s:.1f}" y="290" width="{one_s:.1f}" height="3" fill="{p["fg"]}"/>
    <text x="{PX1 - one_s - 8:.1f}" y="295" text-anchor="end" font-family="{sans}" font-size="12" fill="{p["muted"]}">1 s</text>
    <text x="{PX0}" y="295" font-family="{sans}" font-size="12" fill="{p["muted"]}">Electrode O1, light sleep (N2), participant 1</text>
  </g>
</svg>
'''


def main():
    lo, hi = raw_envelope(PX1 - PX0)
    cl = clean_trace()
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    for name, p in THEMES.items():
        (out / f"banner-{name}.svg").write_text(svg(p, lo, hi, cl), encoding="utf-8")
    print(f"raw range {lo.min():.0f}..{hi.max():.0f} uV; cleaned range {cl.min():.0f}..{cl.max():.0f} uV")


if __name__ == "__main__":
    main()
