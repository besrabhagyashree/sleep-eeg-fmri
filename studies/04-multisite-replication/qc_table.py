"""Study 04: per-participant processing-quality table for the README (quality only, no results).

Reads data/qc_nih/sub-*.csv for every finished participant (the one in progress is left out) and rewrites the block
between <!-- qc:start --> and <!-- qc:end --> in README.md. Exclusion rules as in build_nih.py: rule 4 drops a run
with more than 10% of scalp channels bad; rule 5 drops a participant with more than 25% of epochs rejected.

Usage: python studies/04-multisite-replication/qc_table.py
"""
import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QC = ROOT / "data" / "qc_nih"
STATUS = ROOT / "data" / "status" / "nih.json"
README = HERE / "README.md"
PILOT = {"00002", "00067"}


def row(sub, q):
    ok = q[q.status == "ok"]
    skipped = int(q.status.astype(str).str.startswith("skipped").sum())
    n, bad = int(ok.n_epochs.sum()), int(ok.n_bad_epochs.sum())
    pct = 100 * bad / n if n else float("nan")
    rule4 = int((ok.n_bad_channels > 0.10 * ok.n_scalp_channels).sum())
    dbl = 100 * ok.double_counts_mne.sum() / ok.n_beats_mne.sum()
    runs = f"{len(ok)} of {len(q)}" + (f" ({skipped} skipped)" if skipped else "")
    verdict = "❌ excluded (rule 5)" if pct > 25 else "✅ included"
    return (f"| {sub}{' (pilot)' if sub in PILOT else ''} | {runs} | {n:,} | {pct:.1f}% "
            f"| {ok.n_bad_channels.median():.0f} ({ok.n_bad_channels.max():.0f}) | {ok.heart_rate_bpm_mne.median():.0f} "
            f"| {dbl:.1f}% | {ok.double_counts_refined.sum() / ok.n_beats_refined.sum() * 100:.1f}% "
            f"| {ok.inps_db_mne.median():.1f} ({ok.inps_db_mne.min():.1f}–{ok.inps_db_mne.max():.1f}) "
            f"| {int(ok.tr_irregular.sum())} | {rule4} | {verdict} |")


def main():
    s = json.loads(STATUS.read_text()) if STATUS.exists() else {}
    live = (s.get("current") or {}).get("subject") if not s.get("finished") else None
    rows = [row(p.stem.split("-")[1], pd.read_csv(p)) for p in sorted(QC.glob("sub-*.csv"))
            if p.stem.split("-")[1] != live]
    block = "\n".join([
        "| Participant | Runs processed | Epochs analysed | Rejected | Bad channels, median (max) | Heart rate, bpm "
        "| Double-counted beats, MNE | … refined | INPS dB, median (range) | Irregular volume intervals | Runs dropped (rule 4) "
        "| Status |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|",
        *rows])
    text = README.read_text(encoding="utf-8")
    text = re.sub(r"(<!-- qc:start -->).*?(<!-- qc:end -->)", lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}", text,
                  flags=re.S)
    README.write_text(text, encoding="utf-8")
    print(f"{len(rows)} participants written to {README.name}")


if __name__ == "__main__":
    main()
