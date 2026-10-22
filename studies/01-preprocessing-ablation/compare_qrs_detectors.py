"""Choose the R-peak (QRS) detector for heartbeat-artefact removal among PUBLISHED methods only.

Each detector is run on the same gradient-corrected, filtered in-scanner ECG; its beats drive the
same average artefact subtraction (Allen et al., 1998). Detectors are scored with the standard
BCG-removal metric INPS (improvement in normalised power spectrum; Ghaderi et al., 2010) and
with beat-detection plausibility (double-counted beats, missed-beat gaps).

INPS (Tong et al., 2001, J Neurosci Methods; as used e.g. in the ccICA comparison, 2018): for each
channel, summed power in 1-Hz windows centred on the first five heart-rate harmonics before
removal, divided by the same sum after removal. Reported in dB (10*log10), averaged over channels.
Higher = more cardiac power removed.

Detectors (NeuroKit2 implementations of published algorithms, plus the Teager-energy detector used
in EEG-fMRI work, Kim et al., 2004):
  pantompkins1985, hamilton2002, elgendi2010, engzeemod2012, christov2004, neurokit, teo_kim2004

Usage: python studies/01-preprocessing-ablation/compare_qrs_detectors.py <recording.vhdr> [...]
"""
import sys
from pathlib import Path

import mne
import neurokit2 as nk
import numpy as np
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from preprocessing.mr_artifacts import TARGET_SFREQ, remove_bcg, remove_gradient, volume_onsets  # noqa: E402

NK_METHODS = ["pantompkins1985", "hamilton2002", "elgendi2010", "engzeemod2012", "christov2004", "neurokit"]


def teo_kim2004(ecg, sf):
    """Teager-energy-operator R-peak detection with a 200 ms refractory period."""
    b, a = signal.butter(3, [5, 30], btype="band", fs=sf)
    x = signal.filtfilt(b, a, ecg)
    x, _ = nk.ecg_invert(x, sampling_rate=int(sf))
    teo = np.r_[0, x[1:-1] ** 2 - x[:-2] * x[2:], 0]
    teo = np.convolve(np.clip(teo, 0, None), np.ones(int(0.02 * sf)) / int(0.02 * sf), mode="same")
    pk, _ = signal.find_peaks(teo, height=np.percentile(teo, 99) * 0.3, distance=int(0.2 * sf))
    return pk


def detect(ecg, sf, method):
    if method == "mne":
        r = mne.io.RawArray(ecg[None], mne.create_info(["ECG"], sf, ["ecg"]), verbose="error")
        ev, _, _ = mne.preprocessing.find_ecg_events(r, ch_name="ECG", verbose="error")
        return ev[:, 0] - r.first_samp
    if method == "hybrid_ours":
        from preprocessing.mr_artifacts import r_peaks
        return r_peaks(ecg, sf)
    if method == "teo_kim2004":
        return teo_kim2004(ecg, sf)
    x, _ = nk.ecg_invert(ecg, sampling_rate=int(sf))
    clean_m = method if method in ("pantompkins1985", "hamilton2002", "elgendi2010", "engzeemod2012", "neurokit") else "neurokit"
    xc = nk.ecg_clean(x, sampling_rate=int(sf), method=clean_m)
    _, info = nk.ecg_peaks(xc, sampling_rate=int(sf), method=method)
    return np.asarray(info["ECG_R_Peaks"], dtype=int)


def inps(before, after, hr_hz, sf, n_harmonics=5):
    f, pb = signal.welch(before, fs=sf, nperseg=int(8 * sf), axis=-1)
    _, pa = signal.welch(after, fs=sf, nperseg=int(8 * sf), axis=-1)
    win = np.zeros_like(f, dtype=bool)
    for k in range(1, n_harmonics + 1):
        win |= np.abs(f - k * hr_hz) <= 0.5
    return float(np.mean(10 * np.log10(pb[:, win].sum(1) / pa[:, win].sum(1))))


def main(paths):
    for vhdr in paths:
        raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
        names = raw.ch_names
        on = volume_onsets(raw); d = raw.get_data(); seg = int(np.min(np.diff(on)))
        remove_gradient(d, on)
        r = mne.io.RawArray(d[:, int(on[0]): int(on[-1] + seg)], raw.info.copy(), verbose="error")
        r.set_channel_types({"ECG": "ecg", "EOG": "eog"})
        r.filter(0.3, 40.0, picks="all", verbose="error"); r.resample(TARGET_SFREQ, verbose="error")
        x = r.get_data()
        ecg = x[names.index("ECG")]
        scalp = [i for i, c in enumerate(names) if c not in ("ECG", "EOG")]
        before = x[scalp]
        print(f"\n{Path(vhdr).name}")
        ref = detect(ecg, TARGET_SFREQ, "mne")
        ref_hz = TARGET_SFREQ / np.median(np.diff(ref))      # common reference heart rate for INPS
        print(f"reference heart rate (MNE): {60 * ref_hz:.1f} bpm; INPS evaluated at its first 5 harmonics")
        print(f"{'detector':16s}{'beats':>7s}{'HR bpm':>8s}{'double':>8s}{'missed':>8s}{'INPS dB':>9s}")
        for m in ["mne", "hybrid_ours", "neurokit", "elgendi2010", "teo_kim2004"]:
            try:
                pk = detect(ecg, TARGET_SFREQ, m)
                rr = np.diff(pk); med = np.median(rr)
                after = before.copy(); remove_bcg(after, pk, TARGET_SFREQ)
                hr = 60 * TARGET_SFREQ / med
                print(f"{m:16s}{len(pk):7d}{hr:8.1f}{int(np.sum(rr < .5 * med)):8d}{int(np.sum(rr > 1.5 * med)):8d}"
                      f"{inps(before, after, ref_hz, TARGET_SFREQ):9.2f}")
            except Exception as e:
                print(f"{m:16s} failed: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main(sys.argv[1:])
