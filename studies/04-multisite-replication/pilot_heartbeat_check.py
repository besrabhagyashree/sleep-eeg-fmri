"""Study 04 pilot, amendment 1 open issue: why was heartbeat (BCG) removal weak in sub-00067?

Processing quality only. Uses the saved AAS-cleaned recordings (scalp detector channels + gradient-cleaned ECG,
250 Hz). Per run: ECG quality (R-peak prominence), beat timing from both detectors (RR variability, double
counts), and the residual heartbeat artefact left in the cleaned EEG (heartbeat-locked average, peak-to-peak,
relative to the same average locked to random times).

Usage: python studies/04-multisite-replication/pilot_heartbeat_check.py
Writes results/pilot_heartbeat_check.csv and results/pilot_heartbeat_check.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from preprocessing.mr_artifacts import r_peaks, r_peaks_mne  # noqa: E402

CLEAN = ROOT / "data" / "clean_nih"
OUT = HERE / "results"
SCALP = ["C3", "C4", "O1", "O2", "F3", "F4"]
PRE, POST = 0.2, 0.8                                    # seconds around each beat


def locked_p2p(x, at, sf):
    a, b = int(PRE * sf), int(POST * sf)
    at = at[(at > a) & (at < x.shape[1] - b)]
    seg = np.stack([x[:, t - a:t + b] for t in at])     # beats x channels x samples
    avg = seg.mean(0)
    return float(np.median(np.ptp(avg, axis=1)) * 1e6), avg


def run_check(path, rng):
    raw = mne.io.read_raw_fif(path, preload=True, verbose="error")
    sf = raw.info["sfreq"]
    ecg = raw.get_data(picks=["ECG"])[0]
    scalp = raw.get_data(picks=[c for c in SCALP if c in raw.ch_names])
    out = {"run": path.name.split("_task-sleep_acq-")[0] + " " + path.name.split("acq-")[1][:13]}
    for tag, det in (("mne", r_peaks_mne), ("refined", r_peaks)):
        pk = det(ecg, sf)
        rr = np.diff(pk) / sf
        med = np.median(rr)
        out[f"hr_{tag}"] = 60 / med
        out[f"double_pct_{tag}"] = 100 * np.mean(rr < 0.5 * med)
        out[f"rr_cv_{tag}"] = float(np.std(rr) / np.mean(rr))
        out[f"bcg_residual_uv_{tag}"], avg = locked_p2p(scalp, pk, sf)
        if tag == "refined":
            out["_avg"], out["_pk"] = avg, pk
    rand = np.sort(rng.integers(int(PRE * sf), ecg.size - int(POST * sf), size=len(out["_pk"])))
    out["random_locked_uv"], _ = locked_p2p(scalp, rand, sf)
    out["residual_ratio"] = out["bcg_residual_uv_refined"] / out["random_locked_uv"]
    pk = out["_pk"]
    out["ecg_prominence"] = float(np.median(np.abs(ecg[pk])) / (np.median(np.abs(ecg - np.median(ecg))) + 1e-12))
    out["_ecg"], out["_sf"] = ecg, sf
    return out


def main():
    rng = np.random.default_rng(0)
    rows = [run_check(p, rng) for p in sorted(CLEAN.glob("*_clean-mne_raw.fif"))]
    OUT.mkdir(exist_ok=True)
    tab = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows])
    tab.round(3).to_csv(OUT / "pilot_heartbeat_check.csv", index=False)
    print(tab.round(2).to_string(index=False))
    show = [rows[0]] + [r for r in rows[1:] if r["run"].endswith(("T2340", "T0025"))]
    fig, ax = plt.subplots(len(show), 3, figsize=(16, 3.2 * len(show)), gridspec_kw={"width_ratios": [2.2, 1.4, 1]})
    for i, r in enumerate(show):
        sf, ecg, pk = r["_sf"], r["_ecg"], r["_pk"]
        t0 = int(600 * sf); seg = slice(t0, t0 + int(10 * sf))
        ax[i, 0].plot(np.arange(seg.stop - seg.start) / sf, ecg[seg] * 1e6, lw=0.7, color="#333")
        m = pk[(pk >= seg.start) & (pk < seg.stop)]
        ax[i, 0].plot((m - seg.start) / sf, ecg[m] * 1e6, "o", ms=4, color="#d97706", label="beats (refined)")
        ax[i, 0].set_title(f"{r['run']}: ECG, 10 s", loc="left", fontsize=10); ax[i, 0].set_xlabel("s")
        rr = np.diff(pk) / sf
        ax[i, 1].plot(rr, lw=0.6, color="#2a78d6"); ax[i, 1].set_ylim(0, 2)
        ax[i, 1].set_title(f"beat-to-beat interval (s); double counts MNE {r['double_pct_mne']:.0f}%", loc="left", fontsize=10)
        tt = np.arange(r["_avg"].shape[1]) / sf - PRE
        ax[i, 2].plot(tt, r["_avg"].T * 1e6, lw=0.8)
        ax[i, 2].set_title(f"left in cleaned EEG: {r['bcg_residual_uv_refined']:.1f} µV (×{r['residual_ratio']:.1f} random)",
                           loc="left", fontsize=10)
        ax[i, 2].set_xlabel("s from beat")
    fig.suptitle("Study 04 pilot · heartbeat check (processing quality only)", x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout(); fig.savefig(OUT / "pilot_heartbeat_check.png", dpi=110)


if __name__ == "__main__":
    main()
