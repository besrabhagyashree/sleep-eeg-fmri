"""Data-quality checks for one in-scanner EEG recording, using established methods only.

1. Files       size and MD5 checksum against OpenNeuro's record; header (channels, sampling rate,
               ECG/EOG present, regular scanner triggers); agreement with the dataset's own BIDS
               metadata (task-*_eeg.json).
2. Channels    PREP bad-channel detection (Bigdely-Shamlo et al., 2015, Front. Neuroinform.) via
               PyPREP: flat/NaN, abnormal amplitude (deviation), low correlation, RANSAC.
3. Epochs      Autoreject global peak-to-peak rejection threshold (Jas et al., 2017, NeuroImage),
               learned per recording on its labelled 30-second epochs; an epoch is flagged when it
               exceeds the threshold on a good channel. Epochs the dataset's expert scorer marked
               uncertain or unscorable are excluded before this (handled by the dataset builder).
4. Correction  heartbeat (BCG) removal scored with INPS (Tong et al., 2001, J. Neurosci. Methods):
               power in 1-Hz windows at the first five heart-rate harmonics, before / after, in dB.
               Gradient removal scored by the residual peak at the scanner slice frequency and its
               2nd harmonic (dB above the neighbouring spectrum).

No pass/fail thresholds are invented here: these functions return measurements. Exclusion
decisions use only common conventions and are made in the analysis (see the study README).
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
    return {"file_size_ok": path.stat().st_size == size_remote,
            "file_md5_ok": None if "-" in etag else md5.hexdigest() == etag}   # multipart ETag != MD5


def header_check(raw: mne.io.BaseRaw, onsets: np.ndarray, sidecar: dict | None = None) -> dict:
    sf = raw.info["sfreq"]
    tr = np.diff(onsets) / sf
    out = {"n_channels": len(raw.ch_names), "sfreq": sf,
           "has_ecg_eog": all(c in raw.ch_names for c in SCALP_EXCLUDE),
           "n_volumes": len(onsets), "tr_s": float(np.median(tr)) if len(tr) else np.nan,
           "tr_irregular": int(np.sum(np.abs(tr - np.median(tr)) > 0.01)) if len(tr) else -1}
    if sidecar:   # the dataset's own BIDS description of the recording
        out["sidecar_sfreq"] = sidecar.get("SamplingFrequency")
        out["sidecar_sfreq_matches"] = sidecar.get("SamplingFrequency") == sf
        n_eeg = sum(c not in SCALP_EXCLUDE for c in raw.ch_names)
        out["sidecar_channels_match"] = sidecar.get("EEGChannelCount") == n_eeg
    return out


# ---------------- level 2: channels ----------------
def channel_check(clean: mne.io.BaseRaw, seed: int = 0) -> dict:
    """PREP bad-channel detection on cleaned scalp EEG (0.3-40 Hz, 250 Hz). PREP's high-frequency
    noise criterion uses power above 50 Hz, which the 40 Hz low-pass removed, so it is not used."""
    from pyprep.find_noisy_channels import NoisyChannels
    eeg = clean.copy().pick([c for c in clean.ch_names if c not in SCALP_EXCLUDE])
    eeg.set_channel_types({c: "eeg" for c in eeg.ch_names})
    eeg.set_montage("standard_1020", on_missing="ignore", verbose="error")
    nc = NoisyChannels(eeg, do_detrend=False, random_state=seed)
    nc.find_bad_by_nan_flat(); nc.find_bad_by_deviation(); nc.find_bad_by_correlation()
    try:
        nc.find_bad_by_ransac(channel_wise=False)
        ransac = list(nc.bad_by_ransac)
    except Exception:
        ransac = ["<ransac-failed>"]
    bads = sorted(set(nc.bad_by_nan) | set(nc.bad_by_flat) | set(nc.bad_by_deviation)
                  | set(nc.bad_by_correlation) | set(b for b in ransac if not b.startswith("<")))
    return {"bad_channels": ";".join(bads), "n_bad_channels": len(bads),
            "bad_by_deviation": ";".join(nc.bad_by_deviation),
            "bad_by_correlation": ";".join(nc.bad_by_correlation),
            "bad_by_ransac": ";".join(ransac)}


# ---------------- level 3: epochs ----------------
def epoch_check(clean: mne.io.BaseRaw, epoch_starts_s, bad_channels: list[str], seed: int = 0):
    """Autoreject global threshold learned on this recording's labelled 30-s epochs; an epoch is
    flagged if its peak-to-peak amplitude exceeds the threshold on any good scalp channel."""
    from autoreject import get_rejection_threshold
    picks = [c for c in clean.ch_names if c not in SCALP_EXCLUDE and c not in bad_channels]
    eeg = clean.copy().pick(picks)
    sf = eeg.info["sfreq"]
    events = np.array([[int(round(t * sf)), 0, 1] for t in epoch_starts_s], dtype=int)
    ep = mne.Epochs(eeg, events, tmin=0.0, tmax=30.0 - 1.0 / sf, baseline=None, preload=True,
                    reject_by_annotation=False, verbose="error")
    thr = get_rejection_threshold(ep, random_state=seed, verbose=False)["eeg"]
    ptp = np.ptp(ep.get_data(), axis=2).max(axis=1)
    flags = ptp > thr
    return {"reject_threshold_uv": float(thr * 1e6), "n_epochs": int(len(flags)),
            "n_bad_epochs": int(flags.sum()),
            "pct_bad_epochs": float(100 * flags.mean()) if len(flags) else np.nan}, flags.tolist()


# ---------------- level 4: artefact correction ----------------
def inps_db(before: np.ndarray, after: np.ndarray, hr_hz: float, sfreq: float, n_harmonics: int = 5) -> float:
    """INPS (Tong et al., 2001): per channel, summed power in 1-Hz windows centred on the first
    `n_harmonics` heart-rate harmonics before removal / after removal; dB, mean over channels."""
    f, pb = signal.welch(before, fs=sfreq, nperseg=int(8 * sfreq), axis=-1)
    _, pa = signal.welch(after, fs=sfreq, nperseg=int(8 * sfreq), axis=-1)
    win = np.zeros_like(f, dtype=bool)
    for k in range(1, n_harmonics + 1):
        win |= np.abs(f - k * hr_hz) <= 0.5
    return float(np.mean(10 * np.log10(pb[:, win].sum(1) / pa[:, win].sum(1))))


def heartbeat_detection_stats(peaks: np.ndarray, sfreq: float) -> dict:
    rr = np.diff(peaks)
    med = np.median(rr)
    return {"heart_rate_bpm": float(60.0 * sfreq / med), "n_beats": int(len(peaks)),
            "double_counts": int(np.sum(rr < 0.5 * med)), "missed_beat_gaps": int(np.sum(rr > 1.5 * med))}


def slice_peak_db(x: np.ndarray, sfreq: float, slice_hz: float) -> dict:
    """Residual scanner peak at the slice frequency and its 2nd harmonic, in dB above the median
    power 1-3 Hz either side."""
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
