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
from preprocessing.mr_artifacts import TARGET_SFREQ, r_peaks, remove_bcg, remove_gradient, volume_onsets  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
S3 = "https://s3.amazonaws.com/openneuro.org"
DS = "ds003768"
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "features"
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


def load_labels(sub: str) -> pd.DataFrame:
    path = download(f"{DS}/sourcedata/sub-{sub}-sleep-stage.tsv")
    d = pd.read_csv(path, sep="\t")
    d = pd.DataFrame({"session": d.iloc[:, -3], "t": d.iloc[:, -2].astype(float),
                      "stage_raw": d.iloc[:, -1].astype(str).str.strip()})
    d["stage"] = d.stage_raw.map(STAGE_MAP)          # uncertain / unscorable -> NaN (dropped)
    return d


def to_250(data, info, span):
    r = mne.io.RawArray(data[:, span], info.copy(), verbose="error")
    r.set_channel_types({"ECG": "ecg", "EOG": "eog"})
    r.filter(0.3, 40.0, picks="all", verbose="error")
    r.resample(TARGET_SFREQ, verbose="error")
    return r.get_data()


def process_run(vhdr: Path, labels: pd.DataFrame, sub: str, session: str):
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
    sf = raw.info["sfreq"]
    names = raw.ch_names
    feat_ch = [c for c in names if c != "ECG"]                 # EEG + EOG; ECG never used as a feature
    fi = [names.index(c) for c in feat_ch]
    data = raw.get_data()
    onsets = volume_onsets(raw)
    qc = {"subject": sub, "session": session, "sfreq": sf, "n_volumes": len(onsets)}
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
    remove_gradient(data, onsets)                              # C: full cleaning (in place)
    clean = to_250(data, raw.info, span)
    peaks = r_peaks(clean[names.index("ECG")], TARGET_SFREQ)
    hr = 60.0 / (np.median(np.diff(peaks)) / TARGET_SFREQ) if len(peaks) > 10 else np.nan
    qc["heart_rate_bpm"] = round(float(hr), 1)
    if 40 <= hr <= 120:
        scalp = [i for i, c in enumerate(names) if c not in ("ECG", "EOG")]
        sub_data = clean[scalp]
        remove_bcg(sub_data, peaks, TARGET_SFREQ)
        clean[scalp] = sub_data
        qc["bcg"] = "removed"
    else:
        qc["bcg"] = "skipped: implausible heart rate"
    add("cleaned", clean[fi], TARGET_SFREQ)
    qc.update(status="ok", n_epochs=len(lab))
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
        files = [download(f"{base}_eeg.{ext}") for ext in ("vhdr", "vmrk", "eeg")]
        try:
            r, qc = process_run(files[0], labels, sub, session)
        except Exception as e:                                  # keep going; record the failure
            r, qc = [], {"subject": sub, "session": session, "status": f"error: {e}"}
        qc["seconds"] = round(time.time() - t0)
        rows += r
        qcs.append(qc)
        print(f"sub-{sub} {session}: {qc.get('status')} epochs={qc.get('n_epochs', 0)} "
              f"hr={qc.get('heart_rate_bpm')} {qc['seconds']}s", flush=True)
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
    qc_path = OUT_DIR / "qc.csv"
    for sub in args.subjects:
        qcs = run_subject(sub, args.keep_raw)
        if qcs:
            qc = pd.DataFrame(qcs)
            qc.to_csv(qc_path, mode="a", header=not qc_path.exists(), index=False)


if __name__ == "__main__":
    main()
