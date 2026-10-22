"""Does heartbeat (BCG) removal over-correct, i.e. remove real brain signal?

Test 1, surrogate timing: run the identical subtraction at heartbeat-like times that are NOT
locked to the real heartbeat (shuffled beat-to-beat intervals with a random start). There is no
artefact to find at those times, so the power removed is the method's pure brain-signal loss.

Test 2, physiology: sleep spindles make N2 differ from wake in the sigma band (12-16 Hz).
If cleaning destroyed spindles, the N2-vs-wake sigma contrast would shrink; if it removed
artefact that masks them, the contrast should hold or grow.

Usage: python studies/01-preprocessing-ablation/overcorrection_check.py <recording.vhdr> <stage.tsv>
"""
import sys
from pathlib import Path

import mne
import numpy as np
import pandas as pd
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from preprocessing.mr_artifacts import TARGET_SFREQ, r_peaks, remove_bcg, remove_gradient, volume_onsets  # noqa: E402

BANDS = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 12), "sigma": (12, 16), "beta": (16, 30)}
N_SURROGATES = 20


def band_power(x):
    f, p = signal.welch(x, fs=TARGET_SFREQ, nperseg=int(4 * TARGET_SFREQ), axis=-1)
    return {b: p[:, (f >= lo) & (f < hi)].mean() * 1e12 for b, (lo, hi) in BANDS.items()}


def main(vhdr, tsv):
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
    names = raw.ch_names
    scalp = [i for i, c in enumerate(names) if c not in ("ECG", "EOG")]
    d = raw.get_data()
    on = volume_onsets(raw)
    seg = int(np.min(np.diff(on)))
    remove_gradient(d, on)
    r = mne.io.RawArray(d[:, int(on[0]): int(on[-1] + seg)], raw.info.copy(), verbose="error")
    r.set_channel_types({"ECG": "ecg", "EOG": "eog"})
    r.filter(0.3, 40.0, picks="all", verbose="error"); r.resample(TARGET_SFREQ, verbose="error")
    x = r.get_data()
    before = x[scalp].copy()
    peaks = r_peaks(x[names.index("ECG")], TARGET_SFREQ)
    real = before.copy(); remove_bcg(real, peaks, TARGET_SFREQ)

    pb = band_power(before); pr = band_power(real)
    rng = np.random.default_rng(0)
    rr = np.diff(peaks)
    sur = {b: [] for b in BANDS}
    for _ in range(N_SURROGATES):
        fake = int(rng.integers(0, rr.max())) + np.concatenate([[0], np.cumsum(rng.permutation(rr))])
        fake = fake[fake < before.shape[1]]
        s = before.copy(); remove_bcg(s, fake, TARGET_SFREQ)
        ps = band_power(s)
        for b in BANDS:
            sur[b].append(1 - ps[b] / pb[b])

    print("TEST 1  power removed: real heartbeat times vs surrogate (no-artefact) times")
    print(f"{'band':7s}{'real':>9s}{'surrogate (brain loss)':>26s}{'artefact share of removal':>28s}")
    for b in BANDS:
        real_rm = 1 - pr[b] / pb[b]
        s_mean, s_sd = np.mean(sur[b]), np.std(sur[b])
        print(f"{b:7s}{100 * real_rm:8.1f}%{100 * s_mean:17.1f}% ± {100 * s_sd:.1f}{100 * (1 - s_mean / real_rm):22.0f}%")

    # TEST 2: N2 vs wake contrast in sigma, before vs after
    lab = pd.read_csv(tsv, sep="\t")
    lab = pd.DataFrame({"session": lab.iloc[:, -3], "t": lab.iloc[:, -2], "stage": lab.iloc[:, -1].astype(str).str.strip()})
    run = Path(vhdr).name.split("_eeg")[0].split("_", 1)[1]           # task-sleep_run-1
    lab = lab[(lab.session == run) & lab.stage.isin(["W", "2"])]
    n = int(30 * TARGET_SFREQ)

    def rel_sigma(z, t):
        seg_ = z[:, int(t * TARGET_SFREQ): int(t * TARGET_SFREQ) + n]
        f, p = signal.welch(seg_, fs=TARGET_SFREQ, nperseg=int(4 * TARGET_SFREQ), axis=-1)
        p = p.mean(0)
        return p[(f >= 12) & (f < 16)].sum() / p[(f >= 0.5) & (f < 30)].sum()

    print("\nTEST 2  sigma-band share of 0.5-30 Hz power, N2 vs wake (spindle contrast)")
    print(f"        epochs: wake {(lab.stage == 'W').sum()}, N2 {(lab.stage == '2').sum()}")
    for name, z in (("before heartbeat removal", before), ("after heartbeat removal", real)):
        w = np.mean([rel_sigma(z, t) for t in lab[lab.stage == "W"].t])
        n2 = np.mean([rel_sigma(z, t) for t in lab[lab.stage == "2"].t])
        print(f"        {name:26s} wake {100 * w:5.2f}%  N2 {100 * n2:5.2f}%  N2/wake ratio {n2 / w:.2f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
