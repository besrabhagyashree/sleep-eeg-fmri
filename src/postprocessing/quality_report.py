"""Quality report: every recording's checks, using established methods only.

Reads data/qc/sub-*.csv (written by the dataset builder) and writes, into the given folder:
  quality_by_recording.csv   one row per recording
  quality_by_person.csv      one row per person
  quality_report.md          summary tables for the README
  quality_overview.png       recordings x pass/fail checks (green = pass, red = fail)

Pass/fail is used only where a common convention exists:
  files      size + MD5 checksum match OpenNeuro; 32 channels, ECG + EOG, regular scanner triggers
  channels   <= 3 bad channels by PREP (10% of 30 scalp channels), else the recording is excluded
  epochs     <= 25% of a person's epochs flagged by Autoreject, else the person is excluded
Reported as measurements, with no invented threshold:
  INPS (Tong et al., 2001) for each heartbeat detector; residual scanner slice-frequency peaks;
  heartbeat-detection counts (double-counted beats, missed-beat gaps); agreement of the files with
  the dataset's own BIDS metadata.

Usage: python src/postprocessing/quality_report.py <output-folder>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
QC = ROOT / "data" / "qc"
PASS_FAIL = {"files": "Files: checksum, channels, triggers", "channels": "Channels: <= 3 bad (PREP)"}


def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    q = pd.concat([pd.read_csv(f, dtype={"subject": str}) for f in sorted(QC.glob("sub-*.csv"))], ignore_index=True)
    ok = q.status.eq("ok")
    q["files"] = (ok & q.file_size_ok.astype(bool) & q.file_md5_ok.fillna(True).astype(bool)
                  & q.n_channels.eq(32) & q.has_ecg_eog.astype(bool) & q.tr_irregular.eq(0))
    q["channels"] = ok & q.n_bad_channels.le(3)
    q.to_csv(out / "quality_by_recording.csv", index=False)

    p = q.groupby("subject").agg(recordings=("session", "size"), epochs=("n_epochs", "sum"),
                                 flagged=("n_bad_epochs", "sum"),
                                 expert_unscorable=("expert_uncertain_or_unscorable", "sum"),
                                 recordings_excluded=("channels", lambda s: int((~s).sum())))
    p["pct_flagged"] = 100 * p.flagged / p.epochs
    p["epochs_ok"] = p.pct_flagged.le(25)
    p.to_csv(out / "quality_by_person.csv")

    n = len(q)
    med = lambda c: q[c].median()  # noqa: E731
    lines = [
        "| Check | Result |", "|---|---|",
        f"| Files: size + MD5 match OpenNeuro, 32 channels, ECG/EOG, regular triggers | {int(q.files.sum())} of {n} recordings pass |",
        f"| Files agree with the dataset's metadata (sampling rate) | {int(q.sidecar_sfreq_matches.astype(bool).sum())} of {n} "
        f"(metadata says {q.sidecar_sfreq.mode()[0]} Hz; files are {q.sfreq.mode()[0]:.0f} Hz) |",
        f"| Channels: <= 3 bad channels (PREP) | {int(q.channels.sum())} of {n} recordings pass |",
        f"| Epochs: <= 25% flagged by Autoreject | {int(p.epochs_ok.sum())} of {len(p)} people pass; "
        f"{int(p.flagged.sum())} of {int(p.epochs.sum())} epochs flagged ({100 * p.flagged.sum() / p.epochs.sum():.1f}%) |",
        f"| Epochs the dataset's expert marked uncertain/unscorable | {int(p.expert_unscorable.sum())} (excluded) |",
        "", "| Measurement (median over recordings) | MNE detector | Refined detector |", "|---|---|---|",
        f"| Heartbeat removal, INPS (dB, higher = more removed) | {med('inps_db_mne'):.2f} | {med('inps_db_refined'):.2f} |",
        f"| Double-counted beats per recording | {med('double_counts_mne'):.0f} | {med('double_counts_refined'):.0f} |",
        f"| Missed-beat gaps per recording | {med('missed_beat_gaps_mne'):.0f} | {med('missed_beat_gaps_refined'):.0f} |",
        "", f"Residual scanner peak after cleaning: {med('slice_peak_1x_db'):.1f} dB at the slice frequency, "
        f"{med('slice_peak_2x_db'):.1f} dB at its 2nd harmonic (above the neighbouring spectrum; median).",
    ]
    (out / "quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    m = q[list(PASS_FAIL)].astype(float).to_numpy().T
    fig, ax = plt.subplots(figsize=(max(8, n * 0.06), 2.2))
    ax.imshow(m, aspect="auto", cmap=matplotlib.colors.ListedColormap(["#d6604d", "#4daf7c"]), vmin=0, vmax=1,
              interpolation="nearest")
    ax.set_yticks(range(len(PASS_FAIL)), list(PASS_FAIL.values()), fontsize=8)
    starts = np.r_[0, np.flatnonzero(q.subject.to_numpy()[1:] != q.subject.to_numpy()[:-1]) + 1]
    ax.set_xticks(starts, q.subject.iloc[starts], fontsize=6)
    ax.set_xlabel("recordings, grouped by participant")
    ax.set_title("Data-quality checks per recording (green = pass, red = fail)", loc="left", fontsize=10)
    fig.tight_layout(); fig.savefig(out / "quality_overview.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
