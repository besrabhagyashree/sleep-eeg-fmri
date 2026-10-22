"""The amendment-5 heart-rate check, on inputs with a known answer."""
import numpy as np
import pandas as pd

from hr_check import epoch_heart_rate, within_stage_corr


def test_heart_rate_per_epoch():
    sf = 250.0
    peaks = np.arange(0, 60 * sf, sf)                       # one beat per second for 60 s -> 60 bpm
    hr = epoch_heart_rate(peaks, sf, [0, 30])
    assert np.allclose(hr, 60.0)


def test_too_few_beats_is_missing():
    assert np.isnan(epoch_heart_rate(np.array([0, 250, 500]), 250.0, [0])[0])


def test_slow_heart_called_n2_gives_negative_correlation():
    hr = np.r_[np.linspace(50, 60, 10), np.linspace(70, 80, 10)]
    p = pd.DataFrame({"stage": "W", "hr": hr, "pred": ["N2"] * 10 + ["W"] * 10})
    assert within_stage_corr(p) < -0.8


def test_constant_prediction_cannot_be_scored():
    p = pd.DataFrame({"stage": "W", "hr": np.linspace(50, 80, 20), "pred": "W"})
    assert np.isnan(within_stage_corr(p))
