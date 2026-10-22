"""Per-epoch EEG features, identical for every arm of the comparison.

One 30-second epoch (n_channels x n_samples, volts) -> one feature row. Works at any sampling
rate, so raw 5 kHz data and cleaned 250 Hz data go through exactly the same code.
"""
import numpy as np
from scipy import signal

BANDS = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 12), "sigma": (12, 16), "beta": (16, 30)}
GROUPS = {
    "frontal": ["Fp1", "Fp2", "F3", "F4", "F7", "F8", "Fz", "FC1", "FC2", "FC5", "FC6"],
    "central": ["C3", "C4", "Cz", "CP1", "CP2", "CP5", "CP6"],
    "posterior": ["P3", "P4", "Pz", "P7", "P8", "O1", "O2", "Oz"],
    "temporal": ["T7", "T8", "TP9", "TP10"],
}
EPS = 1e-30


def _hjorth(x):
    dx = np.diff(x, axis=-1)
    ddx = np.diff(dx, axis=-1)
    var, var_d, var_dd = x.var(-1) + EPS, dx.var(-1) + EPS, ddx.var(-1) + EPS
    mobility = np.sqrt(var_d / var)
    complexity = np.sqrt(var_dd / var_d) / mobility
    return mobility, complexity


def epoch_features(x: np.ndarray, sfreq: float, ch_names: list[str]) -> dict:
    """Features for one epoch. x: (n_channels, n_samples) in volts."""
    f, p = signal.welch(x, fs=sfreq, nperseg=int(4 * sfreq), axis=-1)   # 0.25 Hz resolution
    p = p * 1e12                                                          # V^2/Hz -> uV^2/Hz
    df = f[1] - f[0]
    in_range = (f >= 0.5) & (f < 30)
    out = {}
    idx = {c: i for i, c in enumerate(ch_names)}
    for g, chans in GROUPS.items():
        rows = [idx[c] for c in chans if c in idx]
        pg = p[rows].mean(0)
        total = pg[in_range].sum() * df + EPS
        out[f"{g}_logtotal"] = np.log10(total)
        for b, (lo, hi) in BANDS.items():
            bp = pg[(f >= lo) & (f < hi)].sum() * df + EPS
            out[f"{g}_log_{b}"] = np.log10(bp)
            out[f"{g}_rel_{b}"] = bp / total
        cum = np.cumsum(pg[in_range]) / (pg[in_range].sum() + EPS)
        out[f"{g}_sef95"] = f[in_range][np.searchsorted(cum, 0.95).clip(0, in_range.sum() - 1)]
        out[f"{g}_theta_alpha"] = np.log10((out[f"{g}_rel_theta"] + EPS) / (out[f"{g}_rel_alpha"] + EPS))
        mob, comp = _hjorth(x[rows])
        out[f"{g}_hjorth_mob"] = float(np.median(mob))
        out[f"{g}_hjorth_comp"] = float(np.median(comp))
    if "EOG" in idx:   # slow (0.3-2 Hz) and fast (2-8 Hz) eye-channel power
        pe = p[idx["EOG"]]
        out["eog_log_slow"] = np.log10(pe[(f >= 0.3) & (f < 2)].sum() * df + EPS)
        out["eog_log_fast"] = np.log10(pe[(f >= 2) & (f < 8)].sum() * df + EPS)
    return out
