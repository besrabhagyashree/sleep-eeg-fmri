"""Quality report: every recording's checks scored against the pre-set quality rules.

Reads data/qc/sub-*.csv (written by the dataset builder) and writes, into the given folder:
  quality_by_recording.csv   one row per recording, each check marked pass / fail
  quality_by_person.csv      one row per person
  quality_report.md          summary tables for the README
  quality_overview.png       recordings x checks, green = pass, red = fail

Rules (set before the results):
  1 brain-signal loss of heartbeat subtraction <= 5% in every band (surrogate test)
  2 residual heartbeat artefact <= 95th percentile of random-timing averages
  3 <= 3 bad channels per recording (10% of 30 scalp channels)
  4 <= 25% of a person's epochs flagged by Autoreject
Plus integrity checks: file size + MD5, header (32 channels, 5 kHz, ECG/EOG, regular TR),
and heartbeat detection (40-120 bpm, no double counts, within 20 bpm of the person's median).

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

CHECKS = {
    "files": "File size + checksum",
    "header": "Header (channels, rate, triggers)",
    "heartbeat_detection": "Heartbeat detection plausible",
    "rule1_brain_loss": "Rule 1: brain loss <= 5%",
    "rule2_residual_hb": "Rule 2: residual heartbeat <= random",
    "rule3_channels": "Rule 3: <= 3 bad channels",
}


def score(q: pd.DataFrame) -> pd.DataFrame:
    q = q.copy()
    ok = q.status.eq("ok")
    q["files"] = ok & q.file_size_ok.astype(bool) & q.file_md5_ok.fillna(True).astype(bool)
    q["header"] = ok & q.n_channels.eq(32) & q.sfreq.eq(5000) & q.has_ecg_eog.astype(bool) & q.tr_irregular.eq(0)
    person_hr = q.groupby("subject").heart_rate_bpm.transform("median")
    q["heartbeat_detection"] = (ok & q.heart_rate_bpm.between(40, 120) & q.double_counts.fillna(1).eq(0)
                                & (q.heart_rate_bpm - person_hr).abs().le(20))
    q["rule1_brain_loss"] = ok & q.max_band_brain_loss_pct.le(5.0)
    q["rule2_residual_hb"] = ok & q.residual_hb_ptp_uv.le(q.random_locked_ptp_p95_uv)
    q["rule3_channels"] = ok & q.n_bad_channels.le(3)
    return q


def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    q = pd.concat([pd.read_csv(f, dtype={"subject": str}) for f in sorted(QC.glob("sub-*.csv"))], ignore_index=True)
    q = score(q)
    cols = ["subject", "session", "status", *CHECKS, "heart_rate_bpm", "max_band_brain_loss_pct",
            "residual_hb_ptp_uv", "random_locked_ptp_p95_uv", "n_bad_channels", "bad_channels",
            "n_epochs", "n_bad_epochs", "slice_peak_1x_db", "slice_peak_2x_db"]
    q[[c for c in cols if c in q]].to_csv(out / "quality_by_recording.csv", index=False)

    p = q.groupby("subject").agg(recordings=("session", "size"), epochs=("n_epochs", "sum"),
                                 flagged=("n_bad_epochs", "sum"),
                                 recordings_failing_rule3=("rule3_channels", lambda s: int((~s).sum())))
    p["pct_flagged"] = 100 * p.flagged / p.epochs
    p["rule4_epochs"] = p.pct_flagged.le(25)
    p.to_csv(out / "quality_by_person.csv")

    n = len(q)
    lines = ["| Check | Recordings passing |", "|---|---|"]
    for k, label in CHECKS.items():
        lines.append(f"| {label} | {int(q[k].sum())} of {n} ({100 * q[k].mean():.0f}%) |")
    lines.append(f"| Rule 4: <= 25% epochs flagged (per person) | {int(p.rule4_epochs.sum())} of {len(p)} people |")
    extra = [
        "",
        f"Epochs flagged by Autoreject: {int(p.flagged.sum())} of {int(p.epochs.sum())} "
        f"({100 * p.flagged.sum() / p.epochs.sum():.1f}%).",
        f"Median brain-signal loss of heartbeat subtraction: {q.max_band_brain_loss_pct.median():.1f}% "
        f"(worst band per recording). Median residual heartbeat {q.residual_hb_ptp_uv.median():.1f} µV vs "
        f"random-timing {q.random_locked_ptp_p95_uv.median():.1f} µV.",
        f"Residual scanner slice peak: median {q.slice_peak_1x_db.median():.1f} dB above background "
        f"(2nd harmonic {q.slice_peak_2x_db.median():.1f} dB).",
    ]
    (out / "quality_report.md").write_text("\n".join(lines + extra) + "\n", encoding="utf-8")
    print("\n".join(lines + extra))

    m = q[list(CHECKS)].astype(float).to_numpy().T
    fig, ax = plt.subplots(figsize=(max(8, n * 0.06), 3.2))
    ax.imshow(m, aspect="auto", cmap=matplotlib.colors.ListedColormap(["#d6604d", "#4daf7c"]), vmin=0, vmax=1,
              interpolation="nearest")
    ax.set_yticks(range(len(CHECKS)), list(CHECKS.values()), fontsize=8)
    starts = np.r_[0, np.flatnonzero(q.subject.to_numpy()[1:] != q.subject.to_numpy()[:-1]) + 1]
    ax.set_xticks(starts, q.subject.iloc[starts], fontsize=6)
    ax.set_xlabel("recordings, grouped by participant")
    ax.set_title("Data-quality checks per recording (green = pass, red = fail)", loc="left", fontsize=10)
    fig.tight_layout(); fig.savefig(out / "quality_overview.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
