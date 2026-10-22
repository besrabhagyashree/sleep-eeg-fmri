"""Run every stage for one participant before starting the next.

For each participant, in order:
  1 build       scanner + heartbeat cleaning, four arms, quality checks   (build_dataset.py)
  2 full arm    notch, interpolation, both references                     (build_full_stages.py)
  3 events      spindles, slow waves, alpha peak for the four arms        (build_event_features.py)
  4 table       participant table in the study README                     (participant_table.py)
Stages already done are skipped, so the run can be stopped and restarted at any time. The recordings
downloaded in stage 1 are kept until stage 3 has used them, so each recording is downloaded once.

Usage:
  python studies/01-preprocessing-ablation/run_pipeline.py                  # participants 01-33
  python studies/01-preprocessing-ablation/run_pipeline.py --subjects 16 17
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import build_dataset  # noqa: E402
import build_event_features  # noqa: E402
import build_full_stages  # noqa: E402


def stage(sub, n, name, done, fn):
    if done.exists():
        print(f"sub-{sub} [{n}/4] {name}: already done", flush=True)
        return
    t0 = time.time()
    print(f"sub-{sub} [{n}/4] {name}: started", flush=True)
    fn()
    print(f"sub-{sub} [{n}/4] {name}: done in {(time.time() - t0) / 60:.1f} min", flush=True)


def run_participant(sub):
    def build():
        qcs = build_dataset.run_subject(sub, keep_raw=True)          # stage 3 reuses the downloads
        build_dataset.QC_DIR.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(qcs).to_csv(build_dataset.QC_DIR / f"sub-{sub}.csv", index=False)

    def events():
        build_event_features.OUT.mkdir(parents=True, exist_ok=True)
        build_event_features.process_participant(sub).to_csv(build_event_features.OUT / f"sub-{sub}.csv", index=False)

    stage(sub, 1, "build", build_dataset.OUT_DIR / f"sub-{sub}.csv", build)
    stage(sub, 2, "full arm", build_full_stages.OUT / f"sub-{sub}.csv",
          lambda: build_full_stages.process_participant(sub))
    stage(sub, 3, "events", build_event_features.OUT / f"sub-{sub}.csv", events)
    for f in (build_dataset.RAW_DIR / f"sub-{sub}" / "eeg").glob("*_eeg.eeg"):
        f.unlink()                                                    # free the disk once all stages have used it
    print(f"sub-{sub} [4/4] table: updating", flush=True)
    subprocess.run([sys.executable, str(HERE / "participant_table.py")], check=True,
                   stdout=subprocess.DEVNULL, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    print(f"sub-{sub}: all stages done", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="*", default=[f"{i:02d}" for i in range(1, 34)])
    for sub in ap.parse_args().subjects:
        run_participant(sub)


if __name__ == "__main__":
    main()
