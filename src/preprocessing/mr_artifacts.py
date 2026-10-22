"""Remove MRI artefacts from EEG recorded inside the scanner (OpenNeuro ds003768).

Two artefacts dominate EEG recorded during fMRI:

1. Gradient artefact: the scanner's switching gradients induce voltages hundreds of times
   larger than brain activity, repeating every volume (TR). Removed with average artefact
   subtraction (AAS; Allen et al., 2000): for each volume, subtract the mean waveform of
   its neighbouring volumes, aligned on the scanner's R128 volume triggers.
2. Ballistocardiogram (BCG): every heartbeat moves the head and electrodes in the static
   field. Removed with the same idea locked to ECG R-peaks (Allen et al., 1998).

Heartbeat detection: MNE-Python (Gramfort et al., 2013); see r_peaks_mne / r_peaks. Full
citations: REFERENCES.md.

Usage:
    python src/preprocessing/mr_artifacts.py data/raw/sub-01/eeg/sub-01_task-sleep_run-1_eeg.vhdr
Writes a cleaned 250 Hz recording to data/clean/ and diagnostic figures to figures/.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
from scipy import signal

ROOT = Path(__file__).resolve().parents[2]
TARGET_SFREQ = 250.0
GRAD_WINDOW = 21   # volumes averaged per gradient template
BCG_WINDOW = 21    # heartbeats averaged per BCG template


def moving_template(segments: np.ndarray, window: int) -> np.ndarray:
    """Mean of each row's `window` nearest rows (rows = repeats of the artefact)."""
    n = segments.shape[0]
    half = window // 2
    idx = np.arange(n)
    lo = np.clip(idx - half, 0, n)
    hi = np.clip(idx + half + 1, 0, n)
    cs = np.vstack([np.zeros((1, segments.shape[1])), np.cumsum(segments, axis=0)])
    return (cs[hi] - cs[lo]) / (hi - lo)[:, None]


def volume_onsets(raw: mne.io.BaseRaw) -> np.ndarray:
    """Sample indices of the R128 fMRI volume triggers."""
    onsets = [a["onset"] for a in raw.annotations if a["description"].endswith("R128")]
    return np.round(np.asarray(onsets) * raw.info["sfreq"]).astype(int) - raw.first_samp


def remove_gradient(data: np.ndarray, onsets: np.ndarray, window: int = GRAD_WINDOW):
    """AAS gradient correction, in place, channel by channel. Returns segment length."""
    seg_len = int(np.min(np.diff(onsets)))          # one TR, never overlapping
    onsets = onsets[onsets + seg_len <= data.shape[1]]
    take = onsets[:, None] + np.arange(seg_len)[None, :]
    for ch in range(data.shape[0]):
        segs = data[ch, take]
        data[ch, take] = segs - moving_template(segs, window)
    return seg_len, onsets


def _mne_ecg(ecg: np.ndarray, sfreq: float):
    raw = mne.io.RawArray(ecg[None].copy(), mne.create_info(["ECG"], sfreq, ["ecg"]), verbose="error")  # copy: never alter the caller's ECG
    events, _, hr = mne.preprocessing.find_ecg_events(raw, ch_name="ECG", verbose="error")
    return events[:, 0] - raw.first_samp, float(hr)


def heart_rate_mne(ecg: np.ndarray, sfreq: float) -> float:
    """Average heart rate (bpm) from MNE's QRS detector: robust for the rate, imprecise for timing."""
    return _mne_ecg(ecg, sfreq)[1]


def r_peaks_mne(ecg: np.ndarray, sfreq: float) -> np.ndarray:
    """R-peaks exactly as MNE-Python's standard ECG detector returns them (find_ecg_events).

    The established EEG-toolbox method, used unmodified. On this in-scanner ECG it gets the heart
    rate right but double-counts 7-14% of beats (see compare_qrs_detectors.py).
    """
    return _mne_ecg(ecg, sfreq)[0]


def r_peaks(ecg: np.ndarray, sfreq: float) -> np.ndarray:
    """R-peaks with timing refinement: this study's documented adaptation of MNE's detector.

    The heart rate comes from MNE's detector; each beat is placed at the peak of the 8-25 Hz ECG
    energy, with at most one beat per 0.6 beat intervals so a T-wave or an artefact spike cannot
    be counted as an extra beat. Not a published detector; compared against r_peaks_mne in study 01.
    """
    b, a = signal.butter(3, [8, 25], btype="band", fs=sfreq)
    x = signal.filtfilt(b, a, ecg)
    # polarity of in-scanner ECG is arbitrary: use the dominant sign
    if np.abs(np.percentile(x, 0.5)) > np.abs(np.percentile(x, 99.5)):
        x = -x
    energy = np.clip(x, 0, None) ** 2
    hr = heart_rate_mne(ecg, sfreq)
    min_gap = 0.6 * 60.0 / hr if 40 <= hr <= 150 else 0.4      # seconds
    height = np.percentile(energy, 99) * 0.25
    peaks, _ = signal.find_peaks(energy, height=height, distance=int(min_gap * sfreq))
    return peaks


def remove_bcg(data: np.ndarray, peaks: np.ndarray, sfreq: float, window: int = BCG_WINDOW):
    """AAS pulse-artefact correction locked to R-peaks, in place."""
    rr = int(np.median(np.diff(peaks)))
    pre = int(0.25 * rr)
    seg_len = rr
    starts = peaks - pre
    starts = starts[(starts >= 0) & (starts + seg_len <= data.shape[1])]
    take = starts[:, None] + np.arange(seg_len)[None, :]
    for ch in range(data.shape[0]):
        segs = data[ch, take]
        data[ch, take] = segs - moving_template(segs, window)
    return starts, pre, seg_len


def psd(x: np.ndarray, sfreq: float):
    f, p = signal.welch(x, fs=sfreq, nperseg=int(4 * sfreq))
    return f, p


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("vhdr", type=Path)
    ap.add_argument("--show-channel", default="O1")
    args = ap.parse_args()

    stem = args.vhdr.name.replace("_eeg.vhdr", "")
    raw = mne.io.read_raw_brainvision(args.vhdr, preload=True, verbose="error")
    sf = raw.info["sfreq"]
    eeg_picks = [raw.ch_names.index(c) for c in raw.ch_names if c not in ("ECG",)]
    data = raw.get_data()                                   # volts, (n_ch, n_samples)
    show = raw.ch_names.index(args.show_channel)
    ecg_i = raw.ch_names.index("ECG")

    onsets = volume_onsets(raw)
    tr = np.median(np.diff(onsets)) / sf
    print(f"{stem}: {data.shape[0]} ch, {sf:.0f} Hz, {data.shape[1]/sf/60:.1f} min, "
          f"{len(onsets)} volumes, TR = {tr:.3f} s")

    # keep a raw copy of a 10 s window + the show channel for figures
    t0 = int(onsets[len(onsets) // 2])
    win = slice(t0, t0 + int(10 * sf))
    raw_show = data[show].copy()

    # 1) gradient artefact (at full 5 kHz, where the template is sharpest)
    seg_len, used = remove_gradient(data, onsets)
    grad_show = data[show].copy()
    print(f"  gradient AAS: {len(used)} volumes, template window {GRAD_WINDOW}")

    # crop to the scanning period, low-pass and downsample to 250 Hz
    span = slice(int(used[0]), int(used[-1] + seg_len))
    clean = mne.io.RawArray(data[:, span], raw.info.copy(), verbose="error")
    clean.set_channel_types({"ECG": "ecg", "EOG": "eog"})
    clean.filter(0.3, 40.0, picks="all", verbose="error")
    clean.resample(TARGET_SFREQ, verbose="error")
    cd = clean.get_data()

    # 2) ballistocardiogram
    peaks = r_peaks(cd[ecg_i], TARGET_SFREQ)
    hr = 60.0 / (np.median(np.diff(peaks)) / TARGET_SFREQ)
    before_bcg = cd[show].copy()
    sub = cd[eeg_picks]                                      # copy (fancy indexing); written back below
    starts, pre, bcg_len = remove_bcg(sub, peaks, TARGET_SFREQ)
    cd[eeg_picks] = sub
    print(f"  BCG AAS: {len(peaks)} R-peaks, heart rate ~{hr:.0f} bpm")

    out_dir = ROOT / "data" / "clean"
    out_dir.mkdir(parents=True, exist_ok=True)
    clean._data = cd
    clean.save(out_dir / f"{stem}_clean_raw.fif", overwrite=True, verbose="error")

    # ---------- figures ----------
    fig_dir = ROOT / "figures"
    fig_dir.mkdir(exist_ok=True)
    uv = 1e6
    ch = args.show_channel

    # Fig 1: the three stages on the same 10 s
    t = np.arange(win.stop - win.start) / sf
    k0 = int((win.start - span.start) / sf * TARGET_SFREQ)
    k = slice(k0, k0 + int(10 * TARGET_SFREQ))
    tk = np.arange(k.stop - k.start) / TARGET_SFREQ
    fig, ax = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    ax[0].plot(t, raw_show[win] * uv, lw=.4, color="#7a7d8c")
    ax[0].set_title(f"{ch}: raw in-scanner EEG (gradient artefact dominates)")
    ax[1].plot(tk, before_bcg[k] * uv, lw=.7, color="#b53b6d")
    ax[1].set_title("after gradient correction (AAS) + 0.3–40 Hz filter: heartbeat artefact visible")
    ax[2].plot(tk, cd[show, k] * uv, lw=.7, color="#33318a")
    ax[2].set_title("after ballistocardiogram correction: cleaned EEG")
    for a_ in ax: a_.set_ylabel("µV"); a_.grid(alpha=.25)
    ax[2].set_xlabel("time (s)")
    fig.tight_layout(); fig.savefig(fig_dir / f"{stem}_stages.png", dpi=130); plt.close(fig)

    # Fig 2: spectra before / after
    f_r, p_r = psd(raw_show[span], sf)
    f_g, p_g = psd(signal.resample_poly(grad_show[span], 1, int(sf / TARGET_SFREQ)), TARGET_SFREQ)
    f_c, p_c = psd(cd[show], TARGET_SFREQ)
    fig, ax = plt.subplots(figsize=(9, 5))
    m = f_r <= 100
    ax.semilogy(f_r[m], p_r[m] * uv**2, color="#7a7d8c", lw=.8, label="raw")
    ax.semilogy(f_g, p_g * uv**2, color="#b53b6d", lw=.9, label="gradient-corrected")
    ax.semilogy(f_c, p_c * uv**2, color="#33318a", lw=1.2, label="gradient + BCG corrected")
    ax.set_xlim(0, 100); ax.set_xlabel("frequency (Hz)"); ax.set_ylabel("power (µV²/Hz)")
    ax.set_title(f"{ch} power spectrum, {stem}"); ax.legend(); ax.grid(alpha=.25, which="both")
    fig.tight_layout(); fig.savefig(fig_dir / f"{stem}_psd.png", dpi=130); plt.close(fig)

    # Fig 3: heartbeat-locked average before / after BCG correction
    take = starts[:, None] + np.arange(bcg_len)[None, :]
    tb = (np.arange(bcg_len) - pre) / TARGET_SFREQ * 1000
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(tb, before_bcg[take].mean(0) * uv, color="#b53b6d", label="before BCG correction")
    ax.plot(tb, cd[show][take].mean(0) * uv, color="#33318a", label="after BCG correction")
    ax.axvline(0, color="#7a7d8c", ls="--", lw=.8)
    ax.set_xlabel("time from ECG R-peak (ms)"); ax.set_ylabel("µV")
    ax.set_title(f"{ch}: heartbeat-locked average ({len(starts)} beats)")
    ax.legend(); ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(fig_dir / f"{stem}_bcg.png", dpi=130); plt.close(fig)

    # simple quantitative check: residual power at the slice/volume artefact band and BCG amplitude
    def band(f, p, lo, hi): return p[(f >= lo) & (f < hi)].mean()
    print(f"  {ch} mean power 20–40 Hz: raw {band(f_r,p_r,20,40)*uv**2:.1f} -> "
          f"clean {band(f_c,p_c,20,40)*uv**2:.3f} µV²/Hz")
    ptp_b = np.ptp(before_bcg[take].mean(0)) * uv
    ptp_a = np.ptp(cd[show][take].mean(0)) * uv
    print(f"  {ch} heartbeat-locked peak-to-peak: {ptp_b:.1f} -> {ptp_a:.1f} µV")
    print(f"  saved data/clean/{stem}_clean_raw.fif and 3 figures")


if __name__ == "__main__":
    main()
