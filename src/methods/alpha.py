"""Individual alpha measures for study 02.

- Peak alpha frequency (PAF) and centre of gravity (CoG): Savitzky-Golay method of Corcoran et al. (2018),
  via philistine.mne.savgol_iaf with default parameters.
- FOOOF (Donoghue et al., 2020): aperiodic-adjusted alpha peak and aperiodic exponent from a mean Welch spectrum.
- Absolute alpha power, 8 <= f < 12 Hz.
"""
import mne
import numpy as np
from scipy import signal

ALPHA_SEARCH = (7.0, 14.0)


def concat_segments(data, sfreq, starts, seg_s=30.0):
    """Concatenate fixed-length segments (in time order) of a (n_channels, n_samples) array."""
    n = int(round(seg_s * sfreq))
    parts = [data[:, int(round(s * sfreq)): int(round(s * sfreq)) + n] for s in sorted(starts)]
    parts = [p for p in parts if p.shape[1] == n]
    return np.concatenate(parts, axis=1) if parts else np.empty((data.shape[0], 0))


def corcoran_iaf(x, sfreq, ch_names):
    """PAF and CoG (Hz) for a (n_channels, n_samples) array in volts; None where no qualifying peak."""
    from philistine.mne import savgol_iaf
    raw = mne.io.RawArray(x, mne.create_info(ch_names, sfreq, "eeg"), verbose="error")
    try:
        est = savgol_iaf(raw)
    except ValueError:                      # no alpha band could be located: the pre-registered 'no qualifying peak'
        return None, None
    paf, cog = est.PeakAlphaFrequency, est.CenterOfGravity
    return (None if paf is None else float(paf)), (None if cog is None else float(cog))


def spectrum(x, sfreq):
    """Channel-averaged Welch spectrum (4-s Hann windows, 50% overlap), power in uV^2/Hz."""
    f, p = signal.welch(x * 1e6, fs=sfreq, nperseg=int(4 * sfreq), axis=-1)
    return f, p.mean(0)


def fooof_alpha(f, p, fit=(2.0, 40.0)):
    """FOOOF fit: centre frequency and aperiodic-adjusted power of the largest 7-14 Hz peak, aperiodic exponent."""
    from fooof import FOOOF
    fm = FOOOF(verbose=False)
    fm.fit(f, p, list(fit))
    peaks = fm.get_params("peak_params")
    peaks = np.atleast_2d(peaks) if np.size(peaks) else np.empty((0, 3))
    peaks = peaks[(peaks[:, 0] >= ALPHA_SEARCH[0]) & (peaks[:, 0] <= ALPHA_SEARCH[1])] if len(peaks) else peaks
    exp = float(fm.get_params("aperiodic_params", "exponent"))
    if not len(peaks):
        return {"fooof_cf": np.nan, "fooof_power": np.nan, "fooof_exponent": exp}
    best = peaks[peaks[:, 1].argmax()]
    return {"fooof_cf": float(best[0]), "fooof_power": float(best[1]), "fooof_exponent": exp}


def alpha_power(f, p):
    band = (f >= 8) & (f < 12)
    return float(np.log10(p[band].sum() * (f[1] - f[0])))
