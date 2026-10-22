"""Does cleaning remove brain signal? Compare the cleaned scanning period with the scanner-free
stretch recorded before the first fMRI volume (same person, same session, same electrodes).

The pre-scan stretch has no gradient artefact, so it only gets filtering + heartbeat removal.
If gradient cleaning preserves brain activity, both should have similar spectra in 0.5-30 Hz.

Usage: python studies/01-preprocessing-ablation/signal_preservation.py <recording.vhdr>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from preprocessing.mr_artifacts import TARGET_SFREQ, r_peaks, remove_bcg, remove_gradient, volume_onsets  # noqa: E402

BANDS = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 12), "sigma": (12, 16), "beta": (16, 30)}
HERE = Path(__file__).resolve().parent


def filt250(data, info):
    r = mne.io.RawArray(data, info.copy(), verbose="error")
    r.set_channel_types({"ECG": "ecg", "EOG": "eog"})
    r.filter(0.3, 40.0, picks="all", verbose="error")
    r.resample(TARGET_SFREQ, verbose="error")
    return r.get_data()


def debcg(x, names):
    # MNE's ECG detector: our percentile-threshold detector under-detects on short (<1 min) stretches
    tmp = mne.io.RawArray(x, mne.create_info(names, TARGET_SFREQ, ["eeg" if c not in ("ECG", "EOG") else c.lower() for c in names]), verbose="error")
    ev, _, _ = mne.preprocessing.find_ecg_events(tmp, ch_name="ECG", verbose="error")
    peaks = ev[:, 0] - tmp.first_samp
    scalp = [i for i, c in enumerate(names) if c not in ("ECG", "EOG")]
    sub = x[scalp]
    remove_bcg(sub, peaks, TARGET_SFREQ, window=min(21, max(5, len(peaks) // 2 * 2 - 1)))
    x[scalp] = sub
    return x, scalp, len(peaks)


def spectrum(x):
    f, p = signal.welch(x, fs=TARGET_SFREQ, nperseg=int(4 * TARGET_SFREQ), axis=-1)
    return f, p.mean(0) * 1e12


def main(vhdr):
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
    names, sf = raw.ch_names, raw.info["sfreq"]
    data = raw.get_data()
    on = volume_onsets(raw)
    pre_n = int(on[0]) - int(1.0 * sf)                       # stop 1 s before the first volume
    seg = int(np.min(np.diff(on)))

    pre, scalp, n_pre = debcg(filt250(data[:, :pre_n].copy(), raw.info), names)
    remove_gradient(data, on)
    scan_all = filt250(data[:, int(on[0]): int(on[-1] + seg)], raw.info)
    scan, _, _ = debcg(scan_all, names)
    L = pre.shape[1]                                          # same length, right after scanning starts
    first = scan[:, :L]

    f, p_pre = spectrum(pre[scalp]); _, p_first = spectrum(first[scalp]); _, p_all = spectrum(scan[scalp])
    print(f"pre-scan stretch: {pre_n / sf:.1f} s, {n_pre} heartbeats; scanning period {scan.shape[1] / TARGET_SFREQ / 60:.1f} min")
    print(f"{'band':8s}{'pre-scan':>12s}{'first ' + str(round(L / TARGET_SFREQ)) + ' s scan':>18s}{'whole scan':>12s}   (uV^2/Hz, mean of scalp channels)")
    for b, (lo, hi) in BANDS.items():
        m = (f >= lo) & (f < hi)
        print(f"{b:8s}{p_pre[m].mean():12.2f}{p_first[m].mean():18.2f}{p_all[m].mean():12.2f}")

    fig, ax = plt.subplots(figsize=(9, 5))
    m = (f >= 0.5) & (f <= 40)
    ax.semilogy(f[m], p_pre[m], color="#b53b6d", lw=1.6, label=f"before scanning ({pre_n / sf:.0f} s, no scanner artefact)")
    ax.semilogy(f[m], p_first[m], color="#33318a", lw=1.6, label=f"first {L / TARGET_SFREQ:.0f} s of scanning, after cleaning")
    ax.semilogy(f[m], p_all[m], color="#9a9cab", lw=1, label="whole scanning period, after cleaning")
    for lo, hi in BANDS.values():
        ax.axvline(lo, color="#dcdde4", lw=.8)
    ax.set_xlabel("frequency (Hz)"); ax.set_ylabel("power (µV²/Hz), scalp mean")
    ax.set_title(f"Signal preservation check, {Path(vhdr).name.replace('_eeg.vhdr', '')}", loc="left")
    ax.legend(frameon=False); ax.grid(alpha=.25, which="both")
    out = HERE / "results"; out.mkdir(exist_ok=True)
    fig.tight_layout(); fig.savefig(out / "signal_preservation_sub-01.png", dpi=150)


if __name__ == "__main__":
    main(sys.argv[1])
