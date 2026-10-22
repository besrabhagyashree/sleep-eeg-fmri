"""Sleep-event features for every arm (pre-registration amendment 6). Run after build_dataset.py.

Event detectors need each continuous recording, not 30-second pieces. The cleaned arms are read from
the saved cleaned recordings; the raw and filtered arms are rebuilt from the dataset exactly as in
build_dataset.py (same scan span, same filter), which means re-downloading each recording once.
Epochs, labels and quality flags are copied from the main build, so all feature sets share them.

Writes data/features_events/sub-XX.csv (one row per epoch per arm). Skips participants already done.

Usage:
  python studies/01-preprocessing-ablation/build_event_features.py              # every built participant
  python studies/01-preprocessing-ablation/build_event_features.py --subjects 01
"""
import argparse
import re
import sys
import time
from pathlib import Path

import mne
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
from build_dataset import CLEAN_DIR, DS, download, s3_list, to_250  # noqa: E402
from features.events import event_features  # noqa: E402
from preprocessing.mr_artifacts import TARGET_SFREQ, volume_onsets  # noqa: E402

FEAT, OUT = ROOT / "data" / "features", ROOT / "data" / "features_events"


def raw_and_filtered(vhdr):
    """The raw (native rate) and filtered (0.3-40 Hz, 250 Hz) arms over the scan span, as in build_dataset.py."""
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
    data, onsets = raw.get_data(), volume_onsets(raw)
    span = slice(int(onsets[0]), int(onsets[-1] + int(np.min(np.diff(onsets)))))
    return raw.ch_names, {"raw": (data[:, span], raw.info["sfreq"]),
                          "filtered": (to_250(data, raw.info, span), TARGET_SFREQ)}


def process_participant(sub):
    main = pd.read_csv(FEAT / f"sub-{sub}.csv", dtype={"subject": str})
    epochs = main[main.arm == "cleaned_mne"][["subject", "session", "t", "stage", "qc_epoch_bad"]]
    keys = s3_list(f"{DS}/sub-{sub}/eeg/")
    rows = []
    for base in sorted({re.sub(r"_eeg\.(eeg|vhdr|vmrk)$", "", k) for k in keys if "_eeg." in k}):
        session = re.search(r"(task-\w+_run-\d+)", base).group(1)
        ep = epochs[epochs.session == session].reset_index(drop=True)
        if ep.empty:
            continue
        t0 = time.time()
        files = [download(f"{base}_eeg.{ext}") for ext in ("vhdr", "vmrk", "eeg")]
        names, arms = raw_and_filtered(files[0])
        for tag in ("mne", "refined"):
            r = mne.io.read_raw_fif(CLEAN_DIR / f"sub-{sub}_{session}_clean-{tag}_raw.fif", preload=True, verbose="error")
            arms[f"cleaned_{tag}"] = (r.get_data(), r.info["sfreq"])
            assert r.ch_names == names, "cleaned recording channels differ from the raw file"
        for arm, (x, sf) in arms.items():
            rows.append(pd.concat([ep, event_features(x, sf, names, ep.t).assign(arm=arm)], axis=1))
        files[2].unlink(missing_ok=True)
        print(f"sub-{sub} {session}: {len(ep)} epochs x {len(arms)} arms; {time.time() - t0:.0f}s", flush=True)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="*")
    args = ap.parse_args()
    subs = args.subjects or sorted(f.stem.split("-")[1] for f in FEAT.glob("sub-*.csv"))
    OUT.mkdir(parents=True, exist_ok=True)
    for sub in subs:
        if (OUT / f"sub-{sub}.csv").exists():
            print(f"sub-{sub}: already done", flush=True)
            continue
        process_participant(sub).to_csv(OUT / f"sub-{sub}.csv", index=False)


if __name__ == "__main__":
    main()
