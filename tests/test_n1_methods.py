"""Study 01b methods on inputs with a known answer."""
import numpy as np

from features.n1 import alpha_occupancy, eye_features
from methods.hmm import transitions, viterbi

SF = 250.0


def _pink(n, rng, scale=2e-6):
    """1/f background, as in real EEG (white noise would put alpha and theta at equal density)."""
    spec = np.fft.rfft(rng.normal(size=n))
    f = np.fft.rfftfreq(n, 1 / SF)
    spec[1:] /= np.sqrt(f[1:])
    x = np.fft.irfft(spec, n)
    return scale * x / x.std()


def test_alpha_occupancy_counts_alpha_windows():
    t = np.arange(int(30 * SF)) / SF
    rng = np.random.default_rng(0)
    x = _pink(t.size, rng)
    x[: int(10 * SF)] += 20e-6 * np.sin(2 * np.pi * 10 * t[: int(10 * SF)])     # alpha in the first 10 s only
    out = alpha_occupancy(x, SF)
    # 5 of 15 windows carry alpha; single 2-s periodograms also flag ~15% of background windows by chance
    assert 5 / 15 <= out["alpha_occupancy"] <= 0.55
    noise = [alpha_occupancy(_pink(t.size, np.random.default_rng(s)), SF)["alpha_occupancy"] for s in range(20)]
    assert np.mean(noise) < 0.25                                             # 1/f background alone: chance level
    assert out["alpha_occupancy"] > np.mean(noise) + 0.15


def test_theta_rhythm_is_not_alpha():
    t = np.arange(int(30 * SF)) / SF
    x = 20e-6 * np.sin(2 * np.pi * 6 * t)
    out = alpha_occupancy(x, SF)
    assert out["alpha_occupancy"] == 0 and out["alpha_theta_log"] < 0


def test_eye_features_separate_slow_from_fast():
    t = np.arange(int(30 * SF)) / SF
    slow = 50e-6 * np.sin(2 * np.pi * 0.5 * t)
    fast = 5e-6 * np.sin(2 * np.pi * 3 * t)
    f = eye_features(slow, fast, SF)
    assert f["eog_slow_fast_log"] > 1.5 and 90 < f["eog_slow_ptp90"] < 110    # 100 uV peak to peak


def test_transitions_and_viterbi_smooth_an_isolated_flip():
    classes = ["W", "N1", "N2"]
    T, init = transitions([["W"] * 20 + ["N1"] * 20 + ["N2"] * 20], classes)
    assert T[0, 0] > 0.8 and T[0, 2] < 0.1                                    # W rarely jumps to N2
    post = np.array([[0.7, 0.2, 0.1]] * 5 + [[0.45, 0.1, 0.45]] + [[0.7, 0.2, 0.1]] * 5)   # one ambiguous epoch
    path = viterbi(post, np.array([1 / 3] * 3), T, init)
    assert (path == 0).all()                                                  # stays W through the blip


def test_holm_correction_matches_hand_calculation():
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "studies" / "01b-n1-classification"))
    from run_n1 import holm
    # sorted 0.01, 0.03, 0.04 -> x3, x2, x1 = 0.03, 0.06, 0.04 -> monotone 0.03, 0.06, 0.06
    assert np.allclose(holm(np.array([0.01, 0.04, 0.03])), [0.03, 0.06, 0.06])


def test_youden_threshold_finds_the_separating_cut():
    from methods.threshold import youden_threshold
    prob = np.r_[np.linspace(0.05, 0.30, 50), np.linspace(0.35, 0.60, 50)]   # target scores all above 0.33
    t, j = youden_threshold(np.r_[np.zeros(50), np.ones(50)], prob)
    assert 0.30 < t <= 0.35 and j == 1.0                                     # perfect separation, J = 1


def test_decide_lowers_the_bar_for_the_target_class():
    from methods.threshold import decide
    P = np.array([[0.50, 0.30, 0.20],        # argmax W; N1 0.30 >= 0.25 -> N1
                  [0.20, 0.10, 0.70],        # N1 below threshold -> N2
                  [0.60, 0.20, 0.20]])       # N1 below threshold -> W
    assert list(decide(P, ["W", "N1", "N2"], "N1", 0.25)) == ["N1", "N2", "W"]


def test_corner_and_f1_thresholds():
    from methods.threshold import corner_threshold, f1_threshold
    prob = np.r_[np.linspace(0.05, 0.30, 50), np.linspace(0.35, 0.60, 50)]
    y = np.r_[np.zeros(50), np.ones(50)]
    t, d = corner_threshold(y, prob)
    assert 0.30 < t <= 0.35 and d == 0.0
    P = np.column_stack([1 - prob, prob, np.zeros(100)])                  # classes W, N1, N2
    labels = np.where(y == 1, "N1", "W")
    t, f = f1_threshold(P, labels, ["W", "N1", "N2"], "N1")
    assert 0.30 < t <= 0.35 and f == 1.0
