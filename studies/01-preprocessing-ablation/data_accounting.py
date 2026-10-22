"""How much of the data does each cleaning step remove, and what was it?

For one recording, accounts for: recording time cut, samples discarded by resampling, and the
share of signal power removed by each step (gradient subtraction, filtering, heartbeat
subtraction), with the removed power split by frequency band so its importance can be judged.

Usage: python studies/01-preprocessing-ablation/data_accounting.py <recording.vhdr>
"""
import sys
from pathlib import Path

import mne
import numpy as np
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from preprocessing.mr_artifacts import TARGET_SFREQ, r_peaks, remove_bcg, remove_gradient, volume_onsets  # noqa: E402

BANDS = {"<0.3 Hz": (0, 0.3), "delta 0.5-4": (0.5, 4), "theta 4-8": (4, 8), "alpha 8-12": (8, 12),
         "sigma 12-16": (12, 16), "beta 16-30": (16, 30), "30-40": (30, 40), ">40 Hz": (40, 2500)}


def band_power(x, sf):
    f, p = signal.welch(x, fs=sf, nperseg=int(4 * sf), axis=-1)
    df = f[1] - f[0]
    return {b: float(p[:, (f >= lo) & (f < hi)].sum(-1).mean() * df * 1e12) for b, (lo, hi) in BANDS.items()}


def main(vhdr):
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
    names, sf = raw.ch_names, raw.info["sfreq"]
    scalp = [i for i, c in enumerate(names) if c not in ("ECG", "EOG")]
    data = raw.get_data()
    data -= data.mean(1, keepdims=True)                     # electrode offsets carry no information
    on = volume_onsets(raw)
    seg = int(np.min(np.diff(on)))
    span = slice(int(on[0]), int(on[-1] + seg))
    n_total, n_span = data.shape[1], span.stop - span.start

    print("1) RECORDING TIME")
    print(f"   kept {n_span / sf:.1f} s of {n_total / sf:.1f} s -> cut {100 * (1 - n_span / n_total):.1f}% "
          f"(before first / after last scanner volume; these seconds have no sleep labels)")
    print("2) SAMPLES")
    print(f"   {sf:.0f} -> {TARGET_SFREQ:.0f} samples/s: {100 * (1 - TARGET_SFREQ / sf):.0f}% of samples dropped; "
          f"they only described frequencies above 125 Hz")

    raw_seg = data[scalp, span].copy()
    remove_gradient(data, on)
    grad_seg = data[scalp, span].copy()
    removed_grad = raw_seg - grad_seg
    p_raw, p_grad = raw_seg.var(1).mean(), grad_seg.var(1).mean()
    print("3) SIGNAL POWER (mean over 30 scalp channels, scanning period)")
    print(f"   gradient subtraction removed {100 * removed_grad.var(1).mean() / p_raw:.2f}% of raw power")

    bp_g = band_power(grad_seg, sf)
    tot_g = sum(bp_g.values())
    print("   after gradient removal, power by band (share of what remains):")
    for b, v in bp_g.items():
        print(f"      {b:12s} {v:10.1f} uV^2   {100 * v / tot_g:6.2f}%")
    outside = bp_g["<0.3 Hz"] + bp_g[">40 Hz"]
    print(f"   filter 0.3-40 Hz removes {100 * outside / tot_g:.1f}% of that (slow drift + >40 Hz)")

    r = mne.io.RawArray(data[:, span], raw.info.copy(), verbose="error")
    r.set_channel_types({"ECG": "ecg", "EOG": "eog"})
    r.filter(0.3, 40.0, picks="all", verbose="error"); r.resample(TARGET_SFREQ, verbose="error")
    x = r.get_data()
    before = x[scalp].copy()
    peaks = r_peaks(x[names.index("ECG")], TARGET_SFREQ)
    sub = x[scalp]; remove_bcg(sub, peaks, TARGET_SFREQ)
    removed_bcg = before - sub
    print(f"   heartbeat subtraction removed {100 * removed_bcg.var(1).mean() / before.var(1).mean():.1f}% "
          f"of the filtered signal's power ({len(peaks)} beats)")
    bb, ba, br = band_power(before, TARGET_SFREQ), band_power(sub, TARGET_SFREQ), band_power(removed_bcg, TARGET_SFREQ)
    print("   heartbeat subtraction by band:  before -> after   (removed share)")
    for b in ["delta 0.5-4", "theta 4-8", "alpha 8-12", "sigma 12-16", "beta 16-30"]:
        print(f"      {b:12s} {bb[b]:8.1f} -> {ba[b]:8.1f}   ({100 * (1 - ba[b] / bb[b]):5.1f}%)")
    # how periodic is what was removed? correlation of removed signal with its own one-beat-later copy
    rr = int(np.median(np.diff(peaks)))
    lagc = np.mean([np.corrcoef(c[:-rr], c[rr:])[0, 1] for c in removed_bcg])
    print(f"   removed heartbeat component repeats beat-to-beat with correlation {lagc:.2f} "
          f"(brain activity would be ~0; artefact ~1)")
    lagb = np.mean([np.corrcoef(c[:-rr], c[rr:])[0, 1] for c in sub])
    print(f"   cleaned signal beat-to-beat correlation {lagb:.2f}")
    print("4) BRAIN SIGNAL ATTENUATION BY THE METHOD ITSELF")
    print("   each template averages 21 segments including the current one -> ~1/21 = 4.8% of a segment's own "
          "brain signal is subtracted with it (theoretical, for brain activity unrelated to the artefact)")


if __name__ == "__main__":
    main(sys.argv[1])
