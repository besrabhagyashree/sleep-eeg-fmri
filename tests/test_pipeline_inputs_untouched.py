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


def test_header_typo_is_pointed_at_the_real_data_file(tmp_path):
    from build_dataset import fix_header
    (tmp_path / "sub-16_task-rest_run-1_eeg.eeg").write_bytes(b"\0" * 8)
    vhdr = tmp_path / "sub-16_task-rest_run-1_eeg.vhdr"
    vhdr.write_text("[Common Infos]\nDataFile=rsub-16_task-rest_run-1_eeg.eeg\nMarkerFile=x.vmrk\n", encoding="latin-1")
    assert fix_header(vhdr) is True
    assert "DataFile=sub-16_task-rest_run-1_eeg.eeg" in vhdr.read_text(encoding="latin-1")
    assert fix_header(vhdr) is False                                   # correct headers are left alone


def test_label_line_with_space_instead_of_tab(tmp_path, monkeypatch):
    import build_dataset
    f = tmp_path / "labels.tsv"
    f.write_text("session\tepoch_start_time_sec\t30-sec_epoch_sleep_stage\r\n"
                 "task-sleep_run-1\t780\t1\r\ntask-sleep_run-1\t810 W\r\ntask-sleep_run-1\t840\tW (uncertain)\r\n", encoding="utf-8")
    monkeypatch.setattr(build_dataset, "download", lambda key: f)
    d = build_dataset.load_labels("32")
    assert d.t.tolist() == [780.0, 810.0, 840.0]
    assert d.stage_raw.tolist() == ["1", "W", "W (uncertain)"]
    assert d.stage.tolist()[:2] == ["N1", "W"] and d.stage.isna().tolist()[2]


def test_download_retries_after_a_stalled_connection(tmp_path, monkeypatch):
    import io
    import build_dataset
    calls = {"n": 0}

    class Fake(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(url, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("read timed out")
        return Fake(b"eeg-bytes")
    monkeypatch.setattr(build_dataset, "RAW_DIR", tmp_path)
    monkeypatch.setattr(build_dataset.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(build_dataset.time, "sleep", lambda s: None)
    out = build_dataset.download("ds003768/sub-99/eeg/x.eeg")
    assert out.read_bytes() == b"eeg-bytes" and calls["n"] == 2 and not out.with_suffix(".eeg.part").exists()
