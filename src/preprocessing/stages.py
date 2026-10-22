"""Further preprocessing stages, applied to an already artefact-cleaned recording (0.3-40 Hz, 250 Hz).

Order follows the PREP pipeline (Bigdely-Shamlo et al., 2015): remove narrow-band noise, then
repair bad channels, then re-reference.

  4b notch_known_peaks   FIR notch filters (MNE-Python) at frequencies with a known non-brain source:
                         the 2nd harmonic of the scanner slice frequency (35 slices / 2.1 s x 2 = 33.3 Hz)
                         and the 38.5 Hz scanner-room equipment peak seen before scanning started.
  5  interpolate_bad     spherical-spline interpolation of PREP-detected bad channels
                         (Perrin et al., 1989), via MNE-Python.
  6  linked_mastoids     re-reference to the average of TP9 and TP10 (mastoid-adjacent electrodes),
                         the reference convention of clinical sleep scoring (AASM manual).

Full citations: REFERENCES.md.
"""
from __future__ import annotations

import mne

SLICE_2ND_HARMONIC_HZ = 2 * 35 / 2.1      # 33.33 Hz
EQUIPMENT_PEAK_HZ = 38.5
MASTOIDS = ["TP9", "TP10"]


def _eeg_picks(raw):
    return [c for c, t in zip(raw.ch_names, raw.get_channel_types()) if t == "eeg"]


def notch_known_peaks(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    raw = raw.copy()
    raw.notch_filter([SLICE_2ND_HARMONIC_HZ, EQUIPMENT_PEAK_HZ], notch_widths=1.0, picks="eeg",
                     method="fir", verbose="error")
    return raw


def interpolate_bad(raw: mne.io.BaseRaw, bads: list[str]) -> mne.io.BaseRaw:
    raw = raw.copy()
    raw.set_montage("standard_1020", on_missing="ignore", verbose="error")
    raw.info["bads"] = [b for b in bads if b in _eeg_picks(raw)]
    if raw.info["bads"]:
        raw.interpolate_bads(reset_bads=True, method={"eeg": "spline"}, verbose="error")
    return raw


def linked_mastoids(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    raw = raw.copy()
    raw.set_eeg_reference(MASTOIDS, verbose="error")
    return raw


def full_stages(raw: mne.io.BaseRaw, bads: list[str]) -> mne.io.BaseRaw:
    """Steps 4b, 5 and 6 in order."""
    return linked_mastoids(interpolate_bad(notch_known_peaks(raw), bads))
