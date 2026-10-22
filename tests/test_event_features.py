"""Event features on synthetic signals with a known answer."""
import numpy as np

from features.events import alpha_peak_features, event_features, slow_wave_features, spindle_features

SF = 100.0
NAMES = ["F3", "F4", "C3", "C4", "O1", "O2", "TP9", "TP10"]


def _background(seconds, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(0, 5e-6, (len(NAMES), int(seconds * SF)))        # 5 uV noise, in volts


def test_spindles_land_in_the_right_epoch():
    x = _background(90)
    t = np.arange(int(1.0 * SF)) / SF
    burst = 40e-6 * np.sin(2 * np.pi * 13.5 * t) * np.hanning(len(t))   # 1 s, 13.5 Hz, 40 uV
    for onset in (35, 45, 55):                                         # all inside the second epoch
        for c in ("C3", "C4"):
            x[NAMES.index(c), int(onset * SF): int(onset * SF) + len(t)] += burst
    sp = spindle_features(x, SF, NAMES, [0, 30, 60])
    assert sp[1]["sp_density"] > 0
    assert sp[0]["sp_density"] == 0 and sp[2]["sp_density"] == 0
    assert 12 <= sp[1]["sp_freq"] <= 15


def test_slow_waves_detected_where_injected():
    x = _background(60)
    t = np.arange(int(1.25 * SF)) / SF
    wave = -100e-6 * np.sin(2 * np.pi * 0.8 * t)                        # 0.8 Hz, 200 uV peak to peak
    for onset in (5, 12, 20):                                          # first epoch only
        for c in ("F3", "F4"):
            x[NAMES.index(c), int(onset * SF): int(onset * SF) + len(t)] += wave
    sw = slow_wave_features(x, SF, NAMES, [0, 30])
    assert sw[0]["sw_density"] > 0 and sw[1]["sw_density"] == 0


def test_alpha_peak_frequency():
    x = _background(30)
    x[[NAMES.index(c) for c in ("O1", "O2")]] += 20e-6 * np.sin(2 * np.pi * 10.0 * np.arange(x.shape[1]) / SF)
    assert abs(alpha_peak_features(x, SF, NAMES, [0])[0]["alpha_peak_freq"] - 10.0) <= 0.25


def test_derivations_use_the_opposite_mastoid():
    from features.events import _pick
    x = np.zeros((len(NAMES), 10)); x[NAMES.index("C3")] = 3e-6; x[NAMES.index("TP10")] = 1e-6; x[NAMES.index("TP9")] = 2e-6
    d, names = _pick(x, NAMES, ["C3", "C4"])
    assert names == ["C3-M2", "C4-M1"] and np.allclose(d[0], 2.0) and np.allclose(d[1], -2.0)


def test_one_row_per_epoch_and_missing_channels_are_safe():
    df = event_features(_background(60)[:2], SF, NAMES[:2], [0, 30])   # frontal channels, no mastoids
    assert len(df) == 2 and df.sp_density.eq(0).all() and df.alpha_peak_freq.isna().all()


def test_filtering_a_channel_subset_matches_filtering_all():
    import mne
    from build_dataset import to_250
    names = ["C3", "C4", "ECG", "EOG"]
    x = np.random.default_rng(1).normal(0, 1e-5, (4, 5000 * 20))
    info = mne.create_info(names, 5000.0, "eeg")
    full = to_250(x, info, slice(0, x.shape[1]))
    sub = to_250(x[:2], mne.create_info(names[:2], 5000.0, "eeg"), slice(0, x.shape[1]))
    assert np.allclose(full[:2], sub, atol=1e-12)
