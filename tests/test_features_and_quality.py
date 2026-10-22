"""Features and quality metrics against signals with known answers."""
import numpy as np
import pytest

from features.spectral import epoch_features
from preprocessing import quality

SF = 250


def _epoch(ch_names, freq, rng, amp=20e-6):
    t = np.arange(30 * SF) / SF
    x = rng.standard_normal((len(ch_names), t.size)) * 1e-6
    x[:30] += amp * np.sin(2 * np.pi * freq * t)
    return x


@pytest.mark.parametrize("freq,band", [(2, "delta"), (6, "theta"), (10, "alpha"), (14, "sigma"), (22, "beta")])
def test_a_pure_rhythm_lands_in_its_band(ch_names, rng, freq, band):
    f = epoch_features(_epoch(ch_names, freq, rng), SF, [c for c in ch_names if c != "ECG"])
    rel = {b: f[f"posterior_rel_{b}"] for b in ("delta", "theta", "alpha", "sigma", "beta")}
    assert max(rel, key=rel.get) == band


def test_features_do_not_depend_on_sampling_rate(ch_names, rng):
    """Raw (5 kHz) and cleaned (250 Hz) arms must be comparable."""
    t5, t2 = np.arange(30 * 5000) / 5000, np.arange(30 * SF) / SF
    a = epoch_features(np.tile(20e-6 * np.sin(2 * np.pi * 10 * t5), (31, 1)), 5000, ch_names[:31])
    b = epoch_features(np.tile(20e-6 * np.sin(2 * np.pi * 10 * t2), (31, 1)), SF, ch_names[:31])
    assert abs(a["posterior_rel_alpha"] - b["posterior_rel_alpha"]) < 0.01


def test_hjorth_mobility_rises_with_frequency(ch_names, rng):
    lo = epoch_features(_epoch(ch_names, 3, rng), SF, ch_names[:31])["posterior_hjorth_mob"]
    hi = epoch_features(_epoch(ch_names, 20, rng), SF, ch_names[:31])["posterior_hjorth_mob"]
    assert hi > lo


def test_inps_is_zero_when_nothing_is_removed(rng):
    x = rng.standard_normal((4, SF * 120))
    assert quality.inps_db(x, x.copy(), 1.2, SF) == pytest.approx(0.0, abs=1e-9)


def test_inps_follows_the_published_definition(rng):
    """Tong et al. (2001): 1-Hz windows at the first five heart-rate harmonics, before / after."""
    t = np.arange(SF * 120) / SF
    brain = rng.standard_normal((4, t.size))
    cardiac = sum(np.sin(2 * np.pi * k * 1.2 * t) for k in range(1, 6)) * 3
    assert quality.inps_db(brain + cardiac, brain, 1.2, SF) > 10      # large cardiac power removed
    assert quality.inps_db(brain + cardiac, brain + cardiac, 1.2, SF) == pytest.approx(0, abs=1e-9)


def test_heartbeat_stats_count_double_beats():
    peaks = np.arange(0, 250 * 60, 200)                                # 75 bpm, regular
    s = quality.heartbeat_detection_stats(peaks, SF)
    assert s["heart_rate_bpm"] == pytest.approx(75) and s["double_counts"] == 0
    s2 = quality.heartbeat_detection_stats(np.sort(np.r_[peaks, peaks[10] + 60]), SF)
    assert s2["double_counts"] == 1          # an extra beat 60 samples in splits 200 into 60 + 140: one interval < 0.5 x median


def test_slice_peak_is_detected(rng):
    t = np.arange(SF * 60) / SF
    x = rng.standard_normal((4, t.size))
    with_peak = x + 3 * np.sin(2 * np.pi * 33.3 * t)
    assert quality.slice_peak_db(with_peak, SF, 16.65)["slice_peak_2x_db"] > 10
    assert abs(quality.slice_peak_db(x, SF, 16.65)["slice_peak_2x_db"]) < 6
