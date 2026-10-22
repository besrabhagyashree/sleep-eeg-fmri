"""Per-epoch sleep-event features, identical for every arm of the comparison.

Detection runs on a whole continuous recording (the detectors' thresholds use the full signal) and
never sees the expert's stages (hypno=None), so labels cannot leak into the features. Each event is
assigned to the 30-second epoch containing its peak.

  spindles      YASA spindles_detect (Vallat & Walker, 2021; after Lacourse et al., 2019) on C3-M2, C4-M1
  slow waves    YASA sw_detect (criteria after Massimini et al., 2004; Carrier et al., 2011) on F3-M2, F4-M1
  alpha peak    frequency of the 7-13 Hz maximum of the O1-M2 / O2-M1 spectrum (Klimesch, 1999)

Channels are the AASM scoring derivations (Berry et al., 2017), each electrode against the opposite
mastoid (TP9 = M1, TP10 = M2). The recording reference, FCz, sits between Fz and Cz and cancels most
of their sleep activity, so detection is not run on the recorded reference.

Means over events are NaN in epochs without events (the comparison fills them with 0).
Full citations: REFERENCES.md.
"""
import numpy as np
import pandas as pd
import yasa
from scipy import signal

MASTOID = {"1": "TP10", "2": "TP9"}                       # left electrodes -> M2 (TP10), right -> M1 (TP9)
SPINDLE_CH, SW_CH, ALPHA_CH = ["C3", "C4"], ["F3", "F4"], ["O1", "O2"]
ALPHA_RANGE = (7.0, 13.0)
EPOCH_S = 30


def _per_epoch(events, time_col, starts, n_ch, cols, prefix):
    """Density (events per channel per minute) and mean of `cols` for events peaking in each epoch."""
    out = []
    for s in starts:
        e = events[(events[time_col] >= s) & (events[time_col] < s + EPOCH_S)] if events is not None else None
        n = 0 if e is None else len(e)
        row = {f"{prefix}_density": n / max(n_ch, 1) / (EPOCH_S / 60)}
        for c, name in cols.items():
            row[f"{prefix}_{name}"] = float(e[c].mean()) if n else np.nan
        out.append(row)
    return out


def _pick(x, ch_names, wanted):
    """AASM derivations (electrode minus opposite mastoid) for the available channels, in microvolts."""
    rows, names = [], []
    for c in wanted:
        m = MASTOID[str(int(c[-1]) % 2 or 2)] if c[-1].isdigit() else None
        if c in ch_names and m in ch_names:
            rows.append(x[ch_names.index(c)] - x[ch_names.index(m)])
            names.append(f"{c}-{'M1' if m == 'TP9' else 'M2'}")
    return (np.array(rows) * 1e6 if rows else np.empty((0, x.shape[1]))), names   # volts -> microvolts (YASA's unit)


def spindle_features(x, sfreq, ch_names, starts):
    d, names = _pick(x, ch_names, SPINDLE_CH)
    sp = yasa.spindles_detect(d, sfreq, ch_names=names, verbose="error") if names else None
    ev = sp.summary() if sp is not None else None
    return _per_epoch(ev, "Peak", starts, len(names),
                      {"Amplitude": "amp", "Frequency": "freq", "Duration": "dur"}, "sp")


def slow_wave_features(x, sfreq, ch_names, starts):
    d, names = _pick(x, ch_names, SW_CH)
    sw = yasa.sw_detect(d, sfreq, ch_names=names, verbose="error") if names else None
    ev = sw.summary() if sw is not None else None
    return _per_epoch(ev, "NegPeak", starts, len(names), {"PTP": "ptp", "Slope": "slope"}, "sw")


def alpha_peak_features(x, sfreq, ch_names, starts):
    d, names = _pick(x, ch_names, ALPHA_CH)
    out = []
    for s in starts:
        seg = d[:, int(s * sfreq): int((s + EPOCH_S) * sfreq)]
        if not names or seg.shape[1] < 4 * sfreq:
            out.append({"alpha_peak_freq": np.nan, "alpha_peak_logpow": np.nan}); continue
        f, p = signal.welch(seg, fs=sfreq, nperseg=int(4 * sfreq), axis=-1)
        band = (f >= ALPHA_RANGE[0]) & (f <= ALPHA_RANGE[1])
        pm = p.mean(0)[band]
        k = int(np.argmax(pm))
        out.append({"alpha_peak_freq": float(f[band][k]), "alpha_peak_logpow": float(np.log10(pm[k] + 1e-30))})
    return out


def event_features(x: np.ndarray, sfreq: float, ch_names: list[str], starts) -> pd.DataFrame:
    """One row per epoch start (seconds). x: continuous recording, (n_channels, n_samples) in volts."""
    starts = list(starts)
    parts = [spindle_features(x, sfreq, ch_names, starts), slow_wave_features(x, sfreq, ch_names, starts),
             alpha_peak_features(x, sfreq, ch_names, starts)]
    return pd.DataFrame([{**a, **b, **c} for a, b, c in zip(*parts)])
