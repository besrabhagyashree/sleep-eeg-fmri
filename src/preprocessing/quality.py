"""Data-quality checks for one in-scanner EEG recording, at four levels.

1. Files       size and MD5 checksum against OpenNeuro's record; header sanity (channels,
               sampling rate, scanner triggers, regular TR).
2. Channels    PREP-style bad-channel detection (Bigdely-Shamlo et al., 2015) via PyPREP:
               flat/NaN, abnormal amplitude, low correlation with other channels, and
               unpredictability from neighbours (RANSAC).
3. Epochs      a peak-to-peak rejection threshold learned from the data with Autoreject
               (Jas et al., 2017), applied to the labelled 30-second epochs.
4. Correction  residual scanner slice-frequency peaks, residual heartbeat artefact against a
               random-timing baseline, brain-signal loss of the heartbeat subtraction measured
               at random times, and a plausible heart rate.

Each check returns plain numbers; pass/fail is decided by the study's pre-set quality rules.
"""
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

import mne
import numpy as np
from scipy import signal

SCALP_EXCLUDE = ("ECG", "EOG")


# ---------------- level 1: files ----------------
def file_check(path: Path, url: str) -> dict:
    head = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60)
    size_remote = int(head.headers["Content-Length"])
    etag = head.headers.get("ETag", "").strip('"')
    md5 = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 24), b""):
            md5.update(chunk)
    size_ok = path.stat().st_size == size_remote
    if "-" in etag:                       # multipart upload: ETag is not a plain MD5
        md5_ok = None
    else:
        md5_ok = md5.hexdigest() == etag
    return {"file_size_ok": size_ok, "file_md5_ok": md5_ok}


def header_check(raw: mne.io.BaseRaw, onsets: np.ndarray) -> dict:
    sf = raw.info["sfreq"]
    tr = np.diff(onsets) / sf
    return {"n_channels": len(raw.ch_names), "sfreq": sf,
            "has_ecg_eog": all(c in raw.ch_names for c in SCALP_EXCLUDE),
            "n_volumes": len(onsets), "tr_s": float(np.median(tr)) if len(tr) else np.nan,
            "tr_irregular": int(np.sum(np.abs(tr - np.median(tr)) > 0.01)) if len(tr) else -1}


# ---------------- level 2: channels ----------------
def channel_check(clean: mne.io.BaseRaw, seed: int = 0) -> dict:
    """PREP bad-channel detection on the cleaned scalp EEG (0.3-40 Hz, 250 Hz).

    The high-frequency-noise criterion of PREP compares power above 50 Hz, which the 40 Hz
    low-pass has removed, so it is not used.
    """
    from pyprep.find_noisy_channels import NoisyChannels
    eeg = clean.copy().pick([c for c in clean.ch_names if c not in SCALP_EXCLUDE])
    eeg.set_channel_types({c: "eeg" for c in eeg.ch_names})
    eeg.set_montage("standard_1020", on_missing="ignore", verbose="error")
    nc = NoisyChannels(eeg, do_detrend=False, random_state=seed)
    nc.find_bad_by_nan_flat(); nc.find_bad_by_deviation(); nc.find_bad_by_correlation()
    try:
        nc.find_bad_by_ransac(channel_wise=False)
        ransac = nc.bad_by_ransac
    except Exception:                    # RANSAC needs enough good channels; record if it can't run
        ransac = ["<ransac-failed>"]
    bads = sorted(set(nc.bad_by_nan) | set(nc.bad_by_flat) | set(nc.bad_by_deviation)
                  | set(nc.bad_by_correlation) | set(b for b in ransac if not b.startswith("<")))
    return {"bad_channels": ";".join(bads), "n_bad_channels": len(bads),
            "bad_by_deviation": ";".join(nc.bad_by_deviation),
            "bad_by_correlation": ";".join(nc.bad_by_correlation),
            "bad_by_ransac": ";".join(ransac)}


# ---------------- level 3: epochs ----------------
def epoch_check(clean: mne.io.BaseRaw, epoch_starts_s, bad_channels: list[str], seed: int = 0):
    """Learn a global peak-to-peak threshold with Autoreject on 10-s windows of scalp EEG, then
    mark a 30-s labelled epoch bad if 2 or more of its three 10-s windows exceed it on any good
    scalp channel. Returns (summary dict, list of per-epoch bad flags)."""
    from autoreject import get_rejection_threshold
    picks = [c for c in clean.ch_names if c not in SCALP_EXCLUDE and c not in bad_channels]
    eeg = clean.copy().pick(picks)
    windows = mne.make_fixed_length_epochs(eeg, duration=10.0, preload=True, verbose="error")
    thr = get_rejection_threshold(windows, random_state=seed, verbose=False)["eeg"]
    x = eeg.get_data()
    sf = eeg.info["sfreq"]
    flags = []
    for t in epoch_starts_s:
        n_bad = 0
        for k in range(3):
            a = int((t + 10 * k) * sf)
            w = x[:, a: a + int(10 * sf)]
            if w.shape[1] and np.ptp(w, axis=1).max() > thr:
                n_bad += 1
        flags.append(n_bad >= 2)
    flags = np.array(flags, dtype=bool)
    return {"reject_threshold_uv": float(thr * 1e6), "n_epochs": int(len(flags)),
            "n_bad_epochs": int(flags.sum()),
            "pct_bad_epochs": float(100 * flags.mean()) if len(flags) else np.nan}, flags.tolist()


# ---------------- level 4: artefact correction ----------------
def slice_peak_db(x: np.ndarray, sfreq: float, slice_hz: float) -> dict:
    """Height (dB) of residual scanner peaks at the slice frequency and its 2nd harmonic,
    relative to the median power 1-3 Hz either side."""
    f, p = signal.welch(x, fs=sfreq, nperseg=int(8 * sfreq), axis=-1)
    p = p.mean(0)
    out = {}
    for h in (1, 2):
        fc = slice_hz * h
        if fc >= sfreq / 2 - 3:
            continue
        peak = p[np.abs(f - fc) <= 0.25].max()
        side = p[(np.abs(f - fc) >= 1) & (np.abs(f - fc) <= 3)]
        out[f"slice_peak_{h}x_db"] = float(10 * np.log10(peak / np.median(side)))
    return out


def _locked_ptp(x, starts, length):
    take = starts[:, None] + np.arange(length)[None, :]
    return float(np.mean([np.ptp(c[take].mean(0)) for c in x]))


def heartbeat_check(before: np.ndarray, after: np.ndarray, peaks: np.ndarray, sfreq: float,
                    remove_fn, n_surrogates: int = 20, seed: int = 0) -> dict:
    """Residual heartbeat artefact vs random-timing baseline, and brain-signal loss of the
    subtraction measured at random (artefact-free) times."""
    rng = np.random.default_rng(seed)
    rr = np.diff(peaks)
    length = int(np.median(rr))
    starts = peaks - int(0.25 * length)
    starts = starts[(starts >= 0) & (starts + length <= after.shape[1])]
    resid = _locked_ptp(after, starts, length)
    rand = []
    for _ in range(n_surrogates):
        s = rng.integers(0, after.shape[1] - length, size=len(starts))
        rand.append(_locked_ptp(after, s, length))
    f, pb = signal.welch(before, fs=sfreq, nperseg=int(4 * sfreq), axis=-1)
    loss = []
    for _ in range(max(3, n_surrogates // 4)):
        fake = int(rng.integers(0, rr.max())) + np.concatenate([[0], np.cumsum(rng.permutation(rr))])
        fake = fake[fake < before.shape[1]]
        s = before.copy()
        remove_fn(s, fake, sfreq)
        _, ps = signal.welch(s, fs=sfreq, nperseg=int(4 * sfreq), axis=-1)
        band = (f >= 0.5) & (f < 30)
        per_band = []
        for lo, hi in ((0.5, 4), (4, 8), (8, 12), (12, 16), (16, 30)):
            m = (f >= lo) & (f < hi)
            per_band.append(1 - ps[:, m].mean() / pb[:, m].mean())
        loss.append(max(per_band))
    hr = 60.0 * sfreq / np.median(rr)
    return {"heart_rate_bpm": float(hr), "n_beats": int(len(peaks)),
            "missed_beat_gaps": int(np.sum(rr > 1.5 * np.median(rr))),
            "double_counts": int(np.sum(rr < 0.5 * np.median(rr))),
            "residual_hb_ptp_uv": resid * 1e6,
            "random_locked_ptp_p95_uv": float(np.percentile(rand, 95) * 1e6),
            "max_band_brain_loss_pct": float(100 * np.mean(loss))}
