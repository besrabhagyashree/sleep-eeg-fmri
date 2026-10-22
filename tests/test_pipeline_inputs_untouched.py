"""No pipeline step may alter the data it is given (regression tests for the in-place filtering bug)."""
import mne
import numpy as np

from conftest import load_study_module
from preprocessing import stages


def _info(ch_names, sf):
    types = ["ecg" if c == "ECG" else "eog" if c == "EOG" else "eeg" for c in ch_names]
    return mne.create_info(ch_names, sf, types)


def test_build_to_250_leaves_input_unchanged(ch_names, rng):
    b = load_study_module("build_dataset")
    data = rng.standard_normal((len(ch_names), 5000 * 4)) * 1e-5
    before = data.copy()
    b.to_250(data, _info(ch_names, 5000), slice(0, data.shape[1]))
    assert np.array_equal(data, before)


def test_cleaning_effect_to_250_leaves_input_unchanged(ch_names, rng):
    c = load_study_module("cleaning_effect")
    data = rng.standard_normal((len(ch_names), 5000 * 4)) * 1e-5
    before = data.copy()
    c.to_250(data, _info(ch_names, 5000), slice(0, data.shape[1]))
    assert np.array_equal(data, before)


def test_stages_return_new_objects_and_leave_input_unchanged(ch_names, rng):
    raw = mne.io.RawArray(rng.standard_normal((len(ch_names), 250 * 60)) * 1e-5, _info(ch_names, 250), verbose="error")
    before = raw.get_data().copy()
    for out in (stages.notch_known_peaks(raw), stages.interpolate_bad(raw, ["F8"]), stages.linked_mastoids(raw)):
        assert out is not raw
    assert np.array_equal(raw.get_data(), before)


def test_interpolation_repairs_a_dead_channel(ch_names, rng):
    x = rng.standard_normal((len(ch_names), 250 * 30)) * 1e-5
    common = np.sin(2 * np.pi * 10 * np.arange(x.shape[1]) / 250) * 3e-5
    x[:30] += common                                     # shared signal across scalp channels
    x[ch_names.index("F8")] = 0.0                        # dead electrode
    raw = mne.io.RawArray(x, _info(ch_names, 250), verbose="error")
    fixed = stages.interpolate_bad(raw, ["F8"]).get_data(picks=["F8"])[0]
    assert np.std(fixed) > 0                             # rebuilt from neighbours
    assert np.corrcoef(fixed, common)[0, 1] > 0.5


def test_notch_removes_the_known_peaks_only(ch_names, rng):
    t = np.arange(250 * 60) / 250
    x = rng.standard_normal((len(ch_names), t.size)) * 1e-6
    x[:30] += 5e-6 * (np.sin(2 * np.pi * 38.5 * t) + np.sin(2 * np.pi * stages.SLICE_2ND_HARMONIC_HZ * t)
                      + np.sin(2 * np.pi * 10 * t))
    raw = mne.io.RawArray(x, _info(ch_names, 250), verbose="error")
    y = stages.notch_known_peaks(raw).get_data(picks=["O1"])[0]
    spec = lambda s, f: np.abs(np.fft.rfft(s))[int(round(f * 60))]  # noqa: E731  (0.0167 Hz bins)
    o1 = x[ch_names.index("O1")]
    assert spec(y, 38.5) < 0.1 * spec(o1, 38.5)
    assert spec(y, 10) > 0.9 * spec(o1, 10)                # alpha untouched
