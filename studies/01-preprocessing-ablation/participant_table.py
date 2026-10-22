"""One table, one row per participant: data quality and sleep-staging scores in every arm.

Columns per participant:
  quality      recordings, epochs kept / flagged by Autoreject / marked unscorable by the expert,
               worst bad-channel count, median INPS for each heartbeat detector, double-counted beats
  within       within-person preview kappa (train on the person's other recordings, test on one; needs >= 3 recordings;
               logistic regression): wake/N1/N2 and wake vs N2, for each arm
  across       main-analysis kappa (model trained on all OTHER people; logistic regression), for each
               arm, once compare_arms.py has run on the complete build (results/per_subject.csv)

Participants not built yet are listed as "processing". Writes results/participants_table.csv and
results/participants_table.md, and refreshes the table between the markers in this study's README.

Usage: python studies/01-preprocessing-ablation/participant_table.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from compare_arms import ARMS, META, TASKS, make_model, prepare  # noqa: E402

ROOT = HERE.parents[1]
OUT = HERE / "results"
SHORT = {"raw": "raw", "filtered": "filt", "cleaned_mne": "clean-MNE", "cleaned_refined": "clean-ref"}
START, END = "<!-- participants-table:start -->", "<!-- participants-table:end -->"


def within_person(d, feats):
    """Leave-one-recording-out kappa per (task, arm); NaN when the person can't be scored."""
    out = {}
    for task, classes in TASKS.items():
        for arm in ARMS:
            a = d[(d.arm == arm) & d.stage.isin(classes)].reset_index(drop=True)
            runs, y = a.session.to_numpy(), a.stage.to_numpy()
            if a.session.nunique() < 3 or len(set(y)) < 2:      # need >= 3 recordings to train on >= 2
                out[(task, arm)] = np.nan; continue
            X = prepare(a, feats, norm=False, context=True)
            pred = np.empty_like(y)
            for r in np.unique(runs):
                tr, te = runs != r, runs == r
                if len(set(y[tr])) < 2:
                    pred[te] = pd.Series(y[tr]).mode()[0]; continue
                m = make_model("logreg"); m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
            out[(task, arm)] = cohen_kappa_score(y, pred)
    return out


def main():
    across = None
    if (OUT / "per_subject.csv").exists():
        ps = pd.read_csv(OUT / "per_subject.csv", dtype={"subject": str})
        across = ps[ps.model == "logreg"].pivot_table(index="subject", columns=["task", "arm"], values="kappa")
    rows = []
    for i in range(1, 34):
        sub = f"{i:02d}"
        fpath, qpath = ROOT / "data" / "features" / f"sub-{sub}.csv", ROOT / "data" / "qc" / f"sub-{sub}.csv"
        if not (fpath.exists() and qpath.exists()):
            rows.append({"participant": sub, "status": "processing"}); continue
        d = pd.read_csv(fpath, dtype={"subject": str}); q = pd.read_csv(qpath, dtype={"subject": str})
        bad_rec = q[q.n_bad_channels > 3].session.tolist()
        raw_arm = d[d.arm == "raw"]
        n_all = len(raw_arm)
        d = d[~d.session.isin(bad_rec) & ~d.qc_epoch_bad.astype(bool)]
        kept = d[d.arm == "raw"]
        pct_flag = 100 * q.n_bad_epochs.sum() / max(q.n_epochs.sum(), 1)
        row = {"participant": sub,
               "status": "excluded (> 25% epochs flagged)" if pct_flag > 25 else "ok",
               "recordings": len(q), "epochs": n_all, "kept": len(kept),
               "W": int((kept.stage == "W").sum()), "N1": int((kept.stage == "N1").sum()),
               "N2": int((kept.stage == "N2").sum()),
               "flagged_pct": round(pct_flag, 1), "expert_unscorable": int(q.expert_uncertain_or_unscorable.sum()),
               "max_bad_channels": int(q.n_bad_channels.max()),
               "inps_mne_db": round(q.inps_db_mne.median(), 2), "inps_refined_db": round(q.inps_db_refined.median(), 2),
               "double_counts_mne": int(q.double_counts_mne.sum()), "double_counts_refined": int(q.double_counts_refined.sum())}
        feats = [c for c in d.columns if c not in META]
        for (task, arm), k in within_person(d, feats).items():
            row[f"within_{task}_{arm}"] = round(k, 2) if pd.notna(k) else np.nan
        if across is not None and sub in across.index:
            for task in TASKS:
                for arm in ARMS:
                    v = across.loc[sub].get((task, arm), np.nan)
                    row[f"across_{task}_{arm}"] = round(v, 2) if pd.notna(v) else np.nan
        rows.append(row)
        print(f"sub-{sub}: done", flush=True)
    t = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    t.to_csv(OUT / "participants_table.csv", index=False)

    def fmt(v):
        return "–" if pd.isna(v) else (f"{v:.2f}" if isinstance(v, float) else str(v))

    def kappa_cell(v):
        """Colour by the Landis & Koch (1977) agreement bands for Cohen's kappa."""
        if pd.isna(v):
            return "–"
        dot = "⬛" if v <= 0 else "🟥" if v <= .20 else "🟧" if v <= .40 else "🟨" if v <= .60 else "🟩" if v <= .80 else "💚"
        return f"{dot} {v:.2f}"

    def ok(flag):
        return "✅" if flag else "❌"

    done = t[t.status != "processing"]
    n_done = len(done)
    pct = round(100 * n_done / 33)
    md = [f'<img alt="progress" src="https://img.shields.io/badge/participants%20built-{n_done}%20of%2033-{"059669" if n_done == 33 else "d97706"}?style=for-the-badge"> '
          f'<img alt="percent" src="https://img.shields.io/badge/progress-{pct}%25-33318a?style=for-the-badge">', "",
          "**Kappa colours** follow the Landis & Koch (1977) agreement bands: "
          "⬛ ≤ 0 none · 🟥 0.01–0.20 slight · 🟧 0.21–0.40 fair · 🟨 0.41–0.60 moderate · 🟩 0.61–0.80 substantial · 💚 0.81–1.00 almost perfect", ""]

    for scope, label, open_ in (("across", "🎯 Main result: scored by a model trained on all other people", True),
                                ("within", "🔍 Within-person preview: trained on the person's other recordings", False)):
        cols = [c for c in t.columns if c.startswith(scope + "_")]
        md += [f"<details{' open' if open_ else ''}>", f"<summary><b>{label}</b></summary>", ""]
        if not cols:
            md += ["> [!NOTE]", "> Available when all 33 participants are built.", "", "</details>", ""]
            continue
        md += ["Logistic regression · Cohen's kappa vs the expert · – = not scored (fewer than 3 recordings, or only one stage)", "",
               "| # | " + " | ".join(f"{'W/N1/N2' if task == '3class' else 'W vs N2'}<br>{SHORT[a]}" for task in TASKS for a in ARMS) + " |",
               "|:---:|" + ":---:|" * (len(TASKS) * len(ARMS))]
        for _, r in t.iterrows():
            if r.status == "processing":
                continue
            md.append(f"| {r.participant} | " + " | ".join(kappa_cell(r.get(f"{scope}_{task}_{a}")) for task in TASKS for a in ARMS) + " |")
        sub = done[[f"{scope}_{task}_{a}" for task in TASKS for a in ARMS if f"{scope}_{task}_{a}" in done]]
        md += ["| **median** | " + " | ".join(f"**{kappa_cell(sub[c].median())}**" for c in sub.columns) + " |", "", "</details>", ""]

    md += ["<details>", "<summary><b>🩺 Data quality per participant</b></summary>", "",
           "✅/❌ against the pre-set conventions: ≤ 3 bad channels (PREP) per recording; ≤ 25% of epochs flagged (Autoreject). "
           "INPS has no published threshold, so it is shown without a colour.", "",
           "| # | Status | Recordings | Epochs kept<br>(W / N1 / N2) | Flagged | Expert-<br>unscorable | Bad channels<br>(max) | INPS dB<br>MNE / refined | Double-counted beats<br>MNE / refined |",
           "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"]
    for _, r in t.iterrows():
        if r.status == "processing":
            md.append(f"| {r.participant} | ⏳ processing | | | | | | | |"); continue
        md.append(f"| {r.participant} | {ok(r.status == 'ok')} {r.status} | {int(r.recordings)} | {int(r.kept)} ({int(r.W)} / {int(r.N1)} / {int(r.N2)}) | "
                  f"{ok(r.flagged_pct <= 25)} {r.flagged_pct}% | {int(r.expert_unscorable)} | {ok(r.max_bad_channels <= 3)} {int(r.max_bad_channels)} | "
                  f"{fmt(r.inps_mne_db)} / {fmt(r.inps_refined_db)} | {int(r.double_counts_mne)} / {int(r.double_counts_refined)} |")
    md += ["", "</details>"]
    text = "\n".join(md) + "\n"
    (OUT / "participants_table.md").write_text(text, encoding="utf-8")

    readme = HERE / "README.md"
    r = readme.read_text(encoding="utf-8")
    if START in r and END in r:
        r = r.split(START)[0] + START + "\n" + text + END + r.split(END)[1]
        readme.write_text(r, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
