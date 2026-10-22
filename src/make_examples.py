"""Example figures showing what each kind of data in ds003768 looks like (participant 1).

Usage: python src/make_examples.py
Needs: data/clean/sub-01_task-sleep_run-1_clean_raw.fif (from mr_artifacts.py),
       data/raw/sourcedata/sub-01-sleep-stage.tsv, sub-01 T1w and rest run-1 BOLD.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import nibabel as nib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "figures" / "examples"
OUT.mkdir(parents=True, exist_ok=True)

HEMA, EOSIN, GREY = "#33318a", "#b53b6d", "#7a7d8c"
STAGE_ORDER = {"W": 0, "1": 1, "2": 2, "3": 3}
STAGE_NAME = {0: "Wake", 1: "N1", 2: "N2", 3: "N3"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def load_stages():
    d = pd.read_csv(RAW / "sourcedata" / "sub-01-sleep-stage.tsv", sep="\t")
    d = pd.DataFrame({"session": d.iloc[:, -3], "t": d.iloc[:, -2], "stage": d.iloc[:, -1].astype(str).str.strip()})
    d["code"] = d.stage.map(STAGE_ORDER)
    return d


def fig_hypnogram(st):
    order = ["task-rest_run-1", "task-rest_run-2"] + sorted(
        [s for s in st.session.unique() if "sleep" in s], key=lambda s: int(s.split("-")[-1]))
    fig, ax = plt.subplots(figsize=(11, 3.2))
    x0 = 0.0
    for s in order:
        g = st[st.session == s].sort_values("t")
        t = x0 + g.t.values / 60
        ax.step(t, g.code.values, where="post", color=HEMA, lw=1.4)
        ax.axvspan(x0, t[-1] + .5, color=EOSIN if "rest" in s else HEMA, alpha=.05, lw=0)
        ax.text(x0 + .3, -0.55, s.replace("task-", "").replace("_run-", " "), fontsize=8, color=GREY)
        x0 = t[-1] + .5 + 1.0
    ax.set_yticks([0, 1, 2, 3], ["Wake", "N1", "N2", "N3"]); ax.invert_yaxis(); ax.set_ylim(3.3, -0.8)
    ax.set_xlabel("minutes of recording (runs placed back to back; gaps between runs not to scale)")
    ax.set_title("Participant 1: expert sleep-stage scoring, one value per 30 seconds", loc="left")
    fig.tight_layout(); fig.savefig(OUT / "01_hypnogram.png", dpi=150); plt.close(fig)


def fig_epochs(st):
    raw = mne.io.read_raw_fif(ROOT / "data" / "clean" / "sub-01_task-sleep_run-1_clean_raw.fif", preload=True, verbose="error")
    sf = raw.info["sfreq"]
    g = st[st.session == "task-sleep_run-1"].reset_index(drop=True)
    chans = ["F3", "C3", "P3", "O1", "Cz", "Pz", "EOG", "ECG"]
    # display filter only: 0.3-15 Hz keeps alpha, theta, spindles and K-complexes and hides residual scanner peaks (20-48 Hz)
    raw.filter(None, 15.0, picks="all", verbose="error")
    data = raw.get_data(picks=chans) * 1e6
    picks = []
    for want in ("W", "2"):
        rows = g[g.stage == want]
        rows = rows[(rows.t + 30) * sf <= data.shape[1]]
        if len(rows): picks.append((want, float(rows.t.iloc[len(rows) // 2])))
    fig, axes = plt.subplots(1, len(picks), figsize=(13, 6), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, (stage, t0) in zip(axes, picks):
        seg = data[:, int(t0 * sf): int((t0 + 30) * sf)]
        tt = np.arange(seg.shape[1]) / sf
        for i, ch in enumerate(chans):
            scale = {"ECG": 0.1, "EOG": 0.5}.get(ch, 1.0)
            ax.plot(tt, seg[i] * scale - i * 120, lw=.6,
                    color=EOSIN if ch in ("EOG", "ECG") else HEMA)
        ax.set_title(f"{STAGE_NAME[STAGE_ORDER[stage]]}: 30-second epoch at {t0:.0f} s of sleep run 1", loc="left")
        ax.set_xlabel("seconds"); ax.set_xlim(0, 30)
    axes[0].set_yticks([-i * 120 for i in range(len(chans))], [{"ECG": "ECG (÷10)", "EOG": "EOG (÷2)"}.get(c, c) for c in chans])
    axes[0].plot([1, 1], [-len(chans) * 120 + 40, -len(chans) * 120 + 140], color="k", lw=2)
    axes[0].text(1.4, -len(chans) * 120 + 80, "100 µV", fontsize=8)
    fig.suptitle("Cleaned EEG as a sleep scorer sees it (after scanner and heartbeat artefact removal; displayed at 0.3–15 Hz)", x=.01, ha="left")
    fig.tight_layout(); fig.savefig(OUT / "02_eeg_epochs_wake_vs_n2.png", dpi=150); plt.close(fig)
    return picks


def fig_t1():
    img = nib.as_closest_canonical(nib.load(RAW / "sub-01" / "anat" / "sub-01_T1w.nii.gz"))
    v = img.get_fdata(); zooms = img.header.get_zooms()[:3]
    c = [s // 2 for s in v.shape]
    lo, hi = np.percentile(v[v > 0], [1, 99.5])
    views = [("sagittal (side)", v[c[0], :, :].T, zooms[2] / zooms[1]),
             ("coronal (front)", v[:, c[1], :].T, zooms[2] / zooms[0]),
             ("axial (top)", v[:, :, c[2]].T, zooms[1] / zooms[0])]
    fig, ax = plt.subplots(1, 3, figsize=(12, 4.4))
    for a, (name, sl, asp) in zip(ax, views):
        a.imshow(sl, cmap="gray", origin="lower", vmin=lo, vmax=hi, aspect=asp); a.set_title(name); a.axis("off")
    fig.suptitle(f"Participant 1: anatomical MRI (T1-weighted), {v.shape[0]}×{v.shape[1]}×{v.shape[2]} voxels, "
                 f"{zooms[0]:.1f}×{zooms[1]:.1f}×{zooms[2]:.1f} mm", x=.01, ha="left")
    fig.tight_layout(); fig.savefig(OUT / "03_anatomical_t1.png", dpi=150); plt.close(fig)
    return v.shape, zooms


def fig_bold():
    img = nib.as_closest_canonical(nib.load(RAW / "sub-01" / "func" / "sub-01_task-rest_run-1_bold.nii.gz"))
    v = img.get_fdata(dtype=np.float32); tr = float(img.header.get_zooms()[3]) or 2.1
    zooms = img.header.get_zooms()[:3]
    mean = v.mean(-1)
    mask = mean > 0.4 * np.percentile(mean, 99)              # simple intensity brain mask
    gs = v[mask].mean(0)
    gs_pct = (gs - gs.mean()) / gs.mean() * 100
    # posterior region: brain voxels in the back fifth of the brain's extent, middle slices (roughly visual cortex)
    ys = np.where(mask.any(axis=(0, 2)))[0]
    y_cut = ys.min() + int(0.2 * (ys.max() - ys.min()))
    occ = np.zeros_like(mask); occ[:, ys.min(): y_cut, v.shape[2] // 3: 2 * v.shape[2] // 3] = True
    roi = mask & occ
    ts = v[roi].mean(0); ts_pct = (ts - ts.mean()) / ts.mean() * 100
    zroi = int(np.round(np.argwhere(roi)[:, 2].mean()))
    t = np.arange(v.shape[-1]) * tr / 60

    fig = plt.figure(figsize=(12, 6.5))
    zs = np.linspace(v.shape[2] * .3, v.shape[2] * .75, 4).astype(int)
    for i, z in enumerate(zs):
        a = fig.add_subplot(2, 4, i + 1)
        a.imshow(mean[:, :, z].T, cmap="gray", origin="lower"); a.axis("off"); a.set_title(f"axial slice {z}", fontsize=9)
        if abs(z - zroi) <= 2:
            a.contour(roi[:, :, z].T, levels=[.5], colors=[EOSIN], linewidths=.8, origin="lower")
    a = fig.add_subplot(2, 1, 2)
    a.plot(t, ts_pct, color=EOSIN, lw=.9, label="back-of-brain region (outlined in pink)")
    a.plot(t, gs_pct, color=HEMA, lw=1.4, label="whole-brain average (global signal)")
    a.set_xlabel("minutes"); a.set_ylabel("signal change (%)")
    a.legend(loc="lower right", bbox_to_anchor=(1, 1.0), ncol=2, frameon=False, fontsize=9)
    a.set_title("BOLD signal over time, rest run 1", loc="left", fontsize=10)
    fig.suptitle(f"Participant 1: fMRI (BOLD), {v.shape[0]}×{v.shape[1]}×{v.shape[2]} voxels of "
                 f"{zooms[0]:.1f}×{zooms[1]:.1f}×{zooms[2]:.1f} mm, {v.shape[3]} volumes every {tr:.1f} s",
                 x=.01, ha="left")
    fig.tight_layout(); fig.savefig(OUT / "04_fmri_bold.png", dpi=150); plt.close(fig)
    return v.shape, zooms, tr


if __name__ == "__main__":
    st = load_stages()
    fig_hypnogram(st)
    print("epochs:", fig_epochs(st))
    print("T1:", fig_t1())
    print("BOLD:", fig_bold())
    print("stage counts sub-01:", st.stage.value_counts().to_dict())
