"""Validate preprocessing stages 4b, 5 and 6 on one cleaned recording, step by step.

For each step, using established measures only:
  narrow-band peaks   residual peak height (dB above the neighbouring spectrum) at 33.3 and 38.5 Hz
  bad channels        PREP bad-channel count, re-run after the step
  signal              share of 0.5-30 Hz power each step changes (scalp mean)
  physiology          posterior alpha share higher in wake than N2, and central sigma share
                      (spindles) higher in N2 than wake, using the dataset's expert labels

Usage: python studies/01-preprocessing-ablation/validate_stages.py 01 task-sleep_run-3 [mne|refined]
"""
import sys
from pathlib import Path

import mne
import numpy as np
import pandas as pd
from scipy import signal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from preprocessing import quality, stages  # noqa: E402

POSTERIOR = ["P3", "P4", "Pz", "P7", "P8", "O1", "O2", "Oz"]
CENTRAL = ["C3", "C4", "Cz", "CP1", "CP2", "CP5", "CP6"]


def peak_db(x, sf, fc):
    f, p = signal.welch(x, fs=sf, nperseg=int(8 * sf), axis=-1)
    p = p.mean(0)
    return 10 * np.log10(p[np.abs(f - fc) <= 0.25].max() / np.median(p[(np.abs(f - fc) >= 1) & (np.abs(f - fc) <= 3)]))


def band_share(raw, chans, lo, hi, starts):
    x = raw.get_data(picks=[c for c in chans if c in raw.ch_names])
    sf = raw.info["sfreq"]
    out = []
    for t in starts:
        seg = x[:, int(t * sf): int((t + 30) * sf)]
        f, p = signal.welch(seg, fs=sf, nperseg=int(4 * sf), axis=-1)
        p = p.mean(0)
        out.append(p[(f >= lo) & (f < hi)].sum() / p[(f >= 0.5) & (f < 30)].sum())
    return float(np.mean(out)) if out else np.nan


def main(sub, session, tag):
    raw = mne.io.read_raw_fif(ROOT / "data" / "clean" / f"sub-{sub}_{session}_clean-{tag}_raw.fif",
                              preload=True, verbose="error")
    q = pd.read_csv(ROOT / "data" / "qc" / f"sub-{sub}.csv", dtype={"subject": str})
    bads = [b for b in str(q.set_index("session").loc[session, "bad_channels"]).split(";") if b and b != "nan"]
    lab = pd.read_csv(ROOT / "data" / "raw" / "sourcedata" / f"sub-{sub}-sleep-stage.tsv", sep="\t")
    lab = pd.DataFrame({"session": lab.iloc[:, -3], "t": lab.iloc[:, -2], "stage": lab.iloc[:, -1].astype(str).str.strip()})
    lab = lab[lab.session == session]
    w, n2 = lab[lab.stage == "W"].t.tolist(), lab[lab.stage.isin(["2", "3"])].t.tolist()

    steps = [("cleaned (input)", raw)]
    steps.append(("+ 4b notch 33.3 & 38.5 Hz", stages.notch_known_peaks(steps[-1][1])))
    steps.append(("+ 5 interpolate bad", stages.interpolate_bad(steps[-1][1], bads)))
    steps.append(("+ 6 linked mastoids", stages.linked_mastoids(steps[-1][1])))

    print(f"participant {sub}, {session}, heartbeat detector: {tag}; PREP bad channels in input: {bads or 'none'}")
    print(f"labelled epochs: wake {len(w)}, N2 {len(n2)}")
    rows, prev = [], None
    for name, r in steps:
        eeg = r.copy().pick("eeg")
        x = eeg.get_data()
        sf = r.info["sfreq"]
        f, p = signal.welch(x, fs=sf, nperseg=int(4 * sf), axis=-1)
        band = p[:, (f >= 0.5) & (f < 30)].sum(-1)
        changed = np.nan if prev is None else 100 * float(np.mean(np.abs(band - prev) / prev))
        prev = band
        prep = quality.channel_check(r)
        rows.append({"step": name,
                     "peak 33.3 Hz (dB)": round(peak_db(x, sf, stages.SLICE_2ND_HARMONIC_HZ), 1),
                     "peak 38.5 Hz (dB)": round(peak_db(x, sf, stages.EQUIPMENT_PEAK_HZ), 1),
                     "PREP bad": prep["bad_channels"] or "none",
                     "0.5-30 Hz power changed (%)": "–" if np.isnan(changed) else round(changed, 1),
                     "alpha share W / N2 (posterior)": f"{band_share(r, POSTERIOR, 8, 12, w):.3f} / {band_share(r, POSTERIOR, 8, 12, n2):.3f}",
                     "sigma share N2 / W (central)": f"{band_share(r, CENTRAL, 12, 16, n2):.3f} / {band_share(r, CENTRAL, 12, 16, w):.3f}"})
    t = pd.DataFrame(rows)
    print(t.to_string(index=False))
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    t.to_csv(out / f"stages_validation_sub-{sub}_{session}_{tag}.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "mne")
