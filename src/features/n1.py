"""Per-epoch features aimed at stage N1 (study 01b pre-registration, methods A and B).

A. Alpha occupancy (AASM: N1 is scored when alpha rhythm is attenuated for more than half of the epoch).
   On an occipital derivation, each 30-s epoch is split into 15 non-overlapping 2-s windows; a window is
   alpha-present when its mean periodogram density in alpha (8 <= f < 12 Hz) exceeds that in theta
   (4 <= f < 8 Hz), i.e. an alpha peak stands above the 1/f background.
B. Eye movements (AASM: slow eye movements are characteristic of N1). From the EOG, a slow (0.3-1 Hz) and a
   fast (1-5 Hz) component, filtered on the continuous recording.
"""
import numpy as np
from scipy import signal

WIN_S, EPOCH_S = 2.0, 30
THETA, ALPHA = (4.0, 8.0), (8.0, 12.0)
EPS = 1e-30


def _windows(x, sfreq):
    n = int(WIN_S * sfreq)
    k = len(x) // n
    return x[: k * n].reshape(k, n)


def alpha_occupancy(x, sfreq):
    """Fraction of 2-s windows with alpha density > theta density, and median log10(alpha / theta) density."""
    w = _windows(np.asarray(x, float), sfreq)
    f, p = signal.periodogram(w, fs=sfreq, window="hann", axis=-1)
    a = p[:, (f >= ALPHA[0]) & (f < ALPHA[1])].mean(1)
    t = p[:, (f >= THETA[0]) & (f < THETA[1])].mean(1)
    return {"alpha_occupancy": float(np.mean(a > t)), "alpha_theta_log": float(np.median(np.log10((a + EPS) / (t + EPS))))}


def eog_components(eog, sfreq):
    """Slow (0.3-1 Hz) and fast (1-5 Hz) EOG components of a continuous recording (zero-phase FIR)."""
    import mne
    slow = mne.filter.filter_data(eog[None], sfreq, 0.3, 1.0, verbose="error")[0]
    fast = mne.filter.filter_data(eog[None], sfreq, 1.0, 5.0, verbose="error")[0]
    return slow, fast


def eye_features(slow, fast, sfreq):
    """Per-epoch eye-movement features from the epoch's slow and fast EOG components (volts in)."""
    ps, pf = np.mean(slow ** 2) * 1e12, np.mean(fast ** 2) * 1e12            # uV^2
    ptp = np.ptp(_windows(slow, sfreq), axis=1) * 1e6                        # uV
    return {"eog_slow_log": float(np.log10(ps + EPS)), "eog_fast_log": float(np.log10(pf + EPS)),
            "eog_slow_fast_log": float(np.log10((ps + EPS) / (pf + EPS))),
            "eog_slow_ptp90": float(np.percentile(ptp, 90))}
