"""Study 02 alpha measures on synthetic data with a known alpha frequency."""
import numpy as np

from methods.alpha import alpha_power, concat_segments, corcoran_iaf, fooof_alpha, spectrum

SF = 250.0


def _eeg(alpha_hz, seconds=180, n_ch=4, seed=0):
    rng = np.random.default_rng(seed)
    n = int(seconds * SF)
    spec = np.fft.rfft(rng.normal(size=(n_ch, n)), axis=1)
    f = np.fft.rfftfreq(n, 1 / SF)
    spec[:, 1:] /= f[1:]                                         # 1/f^2 background, typical of EEG
    x = np.fft.irfft(spec, n, axis=1)
    x = 10e-6 * x / x.std()
    t = np.arange(n) / SF
    return x + 8e-6 * np.sin(2 * np.pi * alpha_hz * t)


def test_corcoran_finds_the_alpha_frequency():
    paf, cog = corcoran_iaf(_eeg(10.0), SF, ["O1", "O2", "Pz", "Oz"])
    assert abs(paf - 10.0) <= 0.3 and abs(cog - 10.0) <= 0.8


def test_fooof_recovers_peak_and_power_increase():
    f, p = spectrum(_eeg(9.5), SF)
    out = fooof_alpha(f, p)
    assert abs(out["fooof_cf"] - 9.5) <= 0.3 and out["fooof_exponent"] > 1
    assert alpha_power(*spectrum(_eeg(9.5), SF)) > alpha_power(*spectrum(_eeg(9.5) * 0.5, SF))


def test_concat_keeps_only_full_segments_in_time_order():
    x = np.arange(10 * 250).reshape(1, -1).astype(float)
    out = concat_segments(x, 25.0, [60, 0, 90], seg_s=30)          # 90 s segment would run past the end
    assert out.shape[1] == 2 * 750 and out[0, 0] == 0 and out[0, 750] == 60 * 25
