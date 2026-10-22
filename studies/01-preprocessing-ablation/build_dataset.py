"""Build the feature table for the preprocessing comparison (ablation study).

For every labelled 30-second epoch of every recording, compute the SAME features from three
versions of the SAME EEG:
    raw       straight from the dataset: 5 kHz, nothing removed, nothing filtered
    filtered  0.3-40 Hz filter + 250 Hz, no artefact removal
    cleaned   scanner (gradient) + heartbeat (BCG) artefacts removed, same filter + 250 Hz

Recordings are downloaded one at a time and deleted after use, so disk use stays ~0.5 GB.
Output: data/features/sub-XX.csv (one row per epoch per arm) + data/features/qc.csv.

Usage:
    python studies/01-preprocessing-ablation/build_dataset.py                 # all 33 participants (skips finished ones)
    python studies/01-preprocessing-ablation/build_dataset.py --subjects 01   # just one
    python studies/01-preprocessing-ablation/build_dataset.py --keep-raw      # don't delete downloaded EEG
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import mne
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from features.spectral import epoch_features                                   # noqa: E402
from preprocessing.mr_artifacts import (TARGET_SFREQ, heart_rate_mne, r_peaks, r_peaks_mne,  # noqa: E402
                                        remove_bcg, remove_gradient, volume_onsets)
from preprocessing import quality                                      # noqa: E402

SLICES_PER_VOLUME = 35            # from the dataset's BOLD headers (80 x 80 x 35 voxels); slice rate = 35 / TR

ROOT = Path(__file__).resolve().parents[2]
S3 = "https://s3.amazonaws.com/openneuro.org"
DS = "ds003768"
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "features"
QC_DIR = ROOT / "data" / "qc"
CLEAN_DIR = ROOT / "data" / "clean"
EPOCH_S = 30
STAGE_MAP = {"W": "W", "1": "N1", "2": "N2", "3": "N2"}   # N3 (42 epochs in total) merged into N2


def s3_list(prefix: str) -> list[str]:
    keys, token = [], None
    while True:
        url = f"{S3}?list-type=2&prefix={prefix}" + (f"&continuation-token={urllib.parse.quote(token)}" if token else "")
        root = ET.fromstring(urllib.request.urlopen(url, timeout=60).read())
        ns = {"s": root.tag.split("}")[0].strip("{")}
        keys += [c.find("s:Key", ns).text for c in root.findall("s:Contents", ns)]
        if root.find("s:IsTruncated", ns).text != "true":
            return keys
        token = root.find("s:NextContinuationToken", ns).text


def download(key: str) -> Path:
    dest = RAW_DIR / key.removeprefix(f"{DS}/")
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        urllib.request.urlretrieve(f"{S3}/{key}", tmp)
        tmp.replace(dest)
    return dest


def fix_header(vhdr: Path) -> bool:
    """Point a BrainVision header at its own data file when the header names a file that does not exist.

    The dataset has at least one header with a typo in DataFile (sub-16 rest run 1: "rsub-16_..."). Only the
    local copy of the header is corrected; the data file is untouched (its MD5 is still checked).
    """
    text = vhdr.read_text(encoding="latin-1")
    m = re.search(r"^DataFile=(.+)$", text, flags=re.M)
    expected = vhdr.name.replace(".vhdr", ".eeg")
    if m is None or m.group(1).strip() == expected or (vhdr.parent / m.group(1).strip()).exists():
        return False
    vhdr.write_text(text.replace(m.group(0), f"DataFile={expected}"), encoding="latin-1")
    return True


def load_labels(sub: str) -> pd.DataFrame:
    path = download(f"{DS}/sourcedata/sub-{sub}-sleep-stage.tsv")
    d = pd.read_csv(path, sep="\t")
    d = pd.DataFrame({"session": d.iloc[:, -3], "t": d.iloc[:, -2].astype(float),
                      "stage_raw": d.iloc[:, -1].astype(str).str.strip()})
    d["stage"] = d.stage_raw.map(STAGE_MAP)          # uncertain / unscorable -> NaN (dropped)
    return d


def to_250(data, info, span):
    r = mne.io.RawArray(data[:, span].copy(), info.copy(), verbose="error")   # copy: RawArray does not copy, and filter() is in place
    r.set_channel_types({c: t for c, t in {"ECG": "ecg", "EOG": "eog"}.items() if c in r.ch_names})
    r.filter(0.3, 40.0, picks="all", verbose="error")
    r.resample(TARGET_SFREQ, verbose="error")
    return r.get_data()


def process_run(vhdr: Path, labels: pd.DataFrame, sub: str, session: str, eeg_key: str):
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
    sf = raw.info["sfreq"]
    names = raw.ch_names
    feat_ch = [c for c in names if c != "ECG"]                 # EEG + EOG; ECG never used as a feature
    fi = [names.index(c) for c in feat_ch]
    data = raw.get_data()
    onsets = volume_onsets(raw)
    qc = {"subject": sub, "session": session}
    qc.update(quality.file_check(vhdr.with_suffix(".eeg"), f"{S3}/{eeg_key}"))       # level 1
    task = re.search(r"task-(\w+?)_", session).group(1)
    sidecar = json.loads(download(f"{DS}/task-{task}_eeg.json").read_text())
    qc.update(quality.header_check(raw, onsets, sidecar))
    lab_all = labels[labels.session == session]
    qc["expert_uncertain_or_unscorable"] = int(lab_all.stage.isna().sum())          # dataset's own flags
    if len(onsets) < 50:
        qc["status"] = "skipped: too few scanner triggers"
        return [], qc
    seg_len = int(np.min(np.diff(onsets)))
    span = slice(int(onsets[0]), int(onsets[-1] + seg_len))
    n_span = span.stop - span.start
    lab = labels[(labels.session == session) & labels.stage.notna()]
    lab = lab[(lab.t + EPOCH_S) * sf <= n_span]                # epochs fully inside the scan
    rows = []

    def add(arm, arr, rate):
        for _, e in lab.iterrows():
            a = int(round(e.t * rate))
            seg = arr[:, a: a + int(EPOCH_S * rate)]
            rows.append({"subject": sub, "session": session, "t": e.t, "stage": e.stage, "arm": arm,
                         **epoch_features(seg, rate, feat_ch)})

    add("raw", data[fi, span], sf)                             # A: untouched
    add("filtered", to_250(data, raw.info, span)[fi], TARGET_SFREQ)   # B: filter only
    remove_gradient(data, onsets)                              # scanner artefact (shared by C and D)
    grad = to_250(data, raw.info, span)
    ecg = grad[names.index("ECG")]
    scalp = [i for i, c in enumerate(names) if c not in ("ECG", "EOG")]
    before = grad[scalp].copy()
    ref_hz = heart_rate_mne(ecg, TARGET_SFREQ) / 60.0          # common heart rate for INPS
    info250 = mne.create_info(names, TARGET_SFREQ,
                              ["ecg" if c == "ECG" else "eog" if c == "EOG" else "eeg" for c in names])
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    cleaned = {}
    # C: heartbeat removal with MNE's standard detector, unmodified; D: with timing refinement
    for arm, detector in (("cleaned_mne", r_peaks_mne), ("cleaned_refined", r_peaks)):
        x = grad.copy()
        peaks = detector(ecg, TARGET_SFREQ)
        stats = quality.heartbeat_detection_stats(peaks, TARGET_SFREQ)
        tag = arm.split("_")[1]
        qc.update({f"{k}_{tag}": v for k, v in stats.items()})
        if 40 <= stats["heart_rate_bpm"] <= 120:
            s = x[scalp]; remove_bcg(s, peaks, TARGET_SFREQ); x[scalp] = s
            qc[f"inps_db_{tag}"] = quality.inps_db(before, s, ref_hz, TARGET_SFREQ)          # level 4
        else:
            qc[f"bcg_{tag}"] = "skipped: implausible heart rate"
        add(arm, x[fi], TARGET_SFREQ)
        cleaned[arm] = x
        mne.io.RawArray(x.astype(np.float32), info250, verbose="error").save(
            CLEAN_DIR / f"sub-{sub}_{session}_clean-{tag}_raw.fif", overwrite=True, verbose="error")

    # channel and epoch quality on the standard-cleaned recording (MNE detector); used for all arms
    std = mne.io.RawArray(cleaned["cleaned_mne"].astype(np.float32), info250, verbose="error")
    tr = np.median(np.diff(onsets)) / sf
    qc.update(quality.slice_peak_db(cleaned["cleaned_mne"][scalp], TARGET_SFREQ, SLICES_PER_VOLUME / tr))
    qc.update(quality.channel_check(std))                                                       # level 2
    bad_ch = [c for c in qc["bad_channels"].split(";") if c]
    ep, flags = quality.epoch_check(std, lab.t.tolist(), bad_ch)                                # level 3
    qc.update(ep)
    bad_at = dict(zip(lab.t.tolist(), flags))
    for r in rows:
        r["qc_epoch_bad"] = bad_at[r["t"]]
    qc.update(status="ok")
    return rows, qc


def run_subject(sub: str, keep_raw: bool):
    out = OUT_DIR / f"sub-{sub}.csv"
    if out.exists():
        print(f"sub-{sub}: already done", flush=True)
        return []
    labels = load_labels(sub)
    keys = s3_list(f"{DS}/sub-{sub}/eeg/")
    runs = sorted({re.sub(r"_eeg\.(eeg|vhdr|vmrk)$", "", k) for k in keys if "_eeg." in k})
    rows, qcs = [], []
    for base in runs:
        session = re.search(r"(task-\w+_run-\d+)", base).group(1)
        t0 = time.time()
        missing = [ext for ext in ("vhdr", "vmrk", "eeg") if f"{base}_eeg.{ext}" not in keys]
        if missing:                                             # the dataset lacks a file for this run
            qcs.append({"subject": sub, "session": session, "seconds": 0,
                        "status": f"skipped: {', '.join(missing)} file missing from dataset"})
            print(f"sub-{sub} {session}: {qcs[-1]['status']}", flush=True)
            continue
        files = [download(f"{base}_eeg.{ext}") for ext in ("vhdr", "vmrk", "eeg")]
        fixed = fix_header(files[0])
        try:
            r, qc = process_run(files[0], labels, sub, session, f"{base}_eeg.eeg")
        except Exception as e:                                  # keep going; record the failure
            r, qc = [], {"subject": sub, "session": session, "status": f"error: {type(e).__name__}: {e}"}
        qc["header_datafile_fixed"] = fixed
        qc["seconds"] = round(time.time() - t0)
        rows += r
        qcs.append(qc)
        hr_ = qc.get("heart_rate_bpm_mne")
        print(f"sub-{sub} {session}: {qc.get('status')} epochs={qc.get('n_epochs', 0)} "
              f"bad_epochs={qc.get('n_bad_epochs')} bad_ch={qc.get('n_bad_channels')} "
              f"hr={None if hr_ is None else round(hr_, 1)} dbl_mne={qc.get('double_counts_mne')} "
              f"inps_mne={qc.get('inps_db_mne', float('nan')):.2f} inps_ref={qc.get('inps_db_refined', float('nan')):.2f} "
              f"md5={qc.get('file_md5_ok')} {qc['seconds']}s", flush=True)
        if not keep_raw:
            files[2].unlink(missing_ok=True)                    # the big .eeg file
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    return qcs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="*", default=[f"{i:02d}" for i in range(1, 34)])
    ap.add_argument("--keep-raw", action="store_true")
    args = ap.parse_args()
    QC_DIR.mkdir(parents=True, exist_ok=True)
    for sub in args.subjects:
        qcs = run_subject(sub, args.keep_raw)
        if qcs:
            pd.DataFrame(qcs).to_csv(QC_DIR / f"sub-{sub}.csv", index=False)


if __name__ == "__main__":
    main()
