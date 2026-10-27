"""Artefact removal: each test uses a synthetic signal whose correct answer is known."""
import mne
import neurokit2 as nk
import numpy as np

from preprocessing.mr_artifacts import (_mne_ecg, moving_template, r_peaks, r_peaks_mne, remove_bcg,
                                        remove_gradient)


def test_moving_template_is_neighbour_mean():
    segs = np.arange(10, dtype=float)[:, None] * np.ones((10, 4))
    t = moving_template(segs, 3)
    assert np.allclose(t[5], segs[4:7].mean(0))          # middle row: mean of rows 4-6
    assert np.allclose(t[0], segs[0:2].mean(0))          # edge row: only the neighbours that exist


def test_gradient_subtraction_removes_a_repeating_artefact(rng):
    sf, tr, n_vol = 1000, 500, 60                         # samples per volume
    brain = rng.standard_normal((2, tr * n_vol)) * 10e-6
    shape = np.sin(np.linspace(0, 40 * np.pi, tr)) * 2e-3  # identical every volume, 200x larger than brain
    data = brain + np.tile(shape, n_vol)[None, :]
    onsets = np.arange(n_vol) * tr
    remove_gradient(data, onsets)
    resid = data - brain
    assert np.abs(resid).max() < 0.05 * np.abs(shape).max()   # >95% of the artefact gone
    corr = np.corrcoef(data[0], brain[0])[0, 1]
    assert corr > 0.9                                          # brain signal kept


def test_gradient_template_spans_a_full_tr_despite_a_spurious_trigger(rng):
    # ds005127 has runs with a few early or duplicated R128 markers; the template must still cover the whole TR
    tr, n_vol = 500, 60
    brain = rng.standard_normal((1, tr * n_vol)) * 10e-6
    shape = np.sin(np.linspace(0, 40 * np.pi, tr)) * 2e-3
    data = brain + np.tile(shape, n_vol)[None, :]
    onsets = np.sort(np.append(np.arange(n_vol) * tr, [20 * tr + 7]))   # one extra marker 7 samples into volume 20
    seg_len, used = remove_gradient(data, onsets)
    assert seg_len == tr and 20 * tr + 7 not in used
    clean = np.r_[0:19 * tr, 22 * tr:59 * tr]                           # away from the skipped volume
    assert np.abs((data - brain)[0, clean]).max() < 0.05 * np.abs(shape).max()


def test_heartbeat_subtraction_removes_a_pulse_artefact(rng):
    sf, rr, n = 250, 200, 120
    peaks = np.arange(20, rr * n, rr)
    brain = rng.standard_normal((3, rr * n + 100)) * 10e-6
    pulse = np.zeros(brain.shape[1])
    wave = np.hanning(80) * 60e-6
    for p in peaks:
        pulse[p + 20: p + 100] += wave
    data = brain + pulse
    remove_bcg(data, peaks, sf)
    seg = slice(peaks[5], peaks[-5])
    assert np.std((data - brain)[:, seg]) < 0.25 * np.std(pulse[seg])


def _ecg(hr, seconds=120, sf=250):
    return nk.ecg_simulate(duration=seconds, sampling_rate=sf, heart_rate=hr, random_state=1) * 1e-3


def test_refined_detector_counts_each_beat_once():
    """Regression test for the double-counting bug (participant 4: 106 bpm reported instead of 66)."""
    for hr in (55, 72, 95):
        ecg = _ecg(hr)
        peaks = r_peaks(ecg, 250)
        rr = np.diff(peaks)
        assert abs(60 * 250 / np.median(rr) - hr) < 5
        assert np.sum(rr < 0.5 * np.median(rr)) == 0          # no T-waves counted as beats
        assert abs(len(peaks) - hr * 2) <= 4                  # about hr beats per minute for 2 minutes


def test_detector_handles_inverted_ecg():
    ecg = -_ecg(72)                                           # in-scanner ECG polarity is arbitrary
    peaks = r_peaks(ecg, 250)
    assert abs(60 * 250 / np.median(np.diff(peaks)) - 72) < 5


def test_mne_detector_rate_is_plausible():
    peaks = r_peaks_mne(_ecg(72), 250)
    assert 60 < 60 * 250 / np.median(np.diff(peaks)) < 85


def test_mne_helper_does_not_modify_the_ecg():
    ecg = _ecg(72)
    before = ecg.copy()
    _mne_ecg(ecg, 250)
    assert np.array_equal(ecg, before)


def test_raw_array_filter_mutates_input_documenting_the_bug():
    """MNE's RawArray does not copy and filter() works in place: the cause of the in-place bug."""
    x = np.random.default_rng(0).standard_normal((1, 5000)) * 1e-5
    before = x.copy()
    mne.io.RawArray(x, mne.create_info(["a"], 250, ["eeg"]), verbose="error").filter(1, 30, verbose="error")
    assert not np.array_equal(x, before)
