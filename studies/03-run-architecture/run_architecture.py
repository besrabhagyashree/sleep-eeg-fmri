"""Study 03: sleep across rest 1, rest 2, sleep 1, sleep 2 and sleep 3, from the expert labels.

Implements PREREGISTRATION.md: per-run sleep share (primary), stage shares, sleep-onset and N2 latency, stage shifts and
awakenings per hour, deepest stage; Friedman (H1) and Page trend (H2) tests, Holm-corrected secondaries, adjacent-pair
Wilcoxon follow-ups, rest-vs-sleep trait correlation, and an exploratory Ward clustering of per-person profiles.

Usage: python studies/03-run-architecture/run_architecture.py [--group qualified|quality|all]
  qualified (default, amendment 1): the 14 qualified sleepers -> results/
  quality: the 29 who passed study 01's quality rules (the original plan) -> results/quality_passed/
  all: quality exclusions ignored (sensitivity) -> results/sensitivity_all/
Writes per_run.csv and summary.json in the group's folder
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, page_trend_test, spearmanr, wilcoxon
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.metrics import silhouette_score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "studies" / "01-preprocessing-ablation"))
from build_dataset import load_labels  # noqa: E402

RUNS = ["task-rest_run-1", "task-rest_run-2", "task-sleep_run-1", "task-sleep_run-2", "task-sleep_run-3"]
SHORT = ["rest 1", "rest 2", "sleep 1", "sleep 2", "sleep 3"]
LENGTH = {r: (600 if "rest" in r else 900) for r in RUNS}     # seconds (task sidecars)
STAGES = {"W": "W", "1": "N1", "2": "N2", "3": "N3"}          # N3 kept separate here; uncertain / unscorable dropped
DEPTH = {"W": 0, "N1": 1, "N2": 2, "N3": 3}
EXCLUDED = {"03", "13", "17", "31"}                           # study 01, rule 5
SLEEPERS = {"01", "04", "07", "09", "11", "14", "15", "16", "18", "19", "23", "24", "25", "27"}   # passed quality, awake < 50%
GROUPS = {"qualified": "", "quality": "quality_passed", "all": "sensitivity_all"}
EPOCH = 30


def run_measures(lab, run):
    g = lab[lab.session == run].sort_values("t")
    st = g.stage_raw.map(STAGES)
    t = g.t[st.notna()].to_numpy()
    s = st.dropna().to_numpy()
    hours = len(s) * EPOCH / 3600
    sleep = s != "W"
    first = lambda m: (float(t[m][0]) if m.any() else float(LENGTH[run])) if len(s) else np.nan   # censored at the run length; NaN if nothing scored
    out = {"run": SHORT[RUNS.index(run)], "n_scored": len(s), "n_uncertain": int(st.isna().sum()),
           "sleep_share": float(sleep.mean()) if len(s) else np.nan,
           **{f"{k}_share": float((s == k).mean()) if len(s) else np.nan for k in DEPTH},
           "sleep_latency_s": first(sleep), "n2_latency_s": first(np.isin(s, ["N2", "N3"])),
           "slept": bool(sleep.any()),
           "shifts_per_h": float((s[1:] != s[:-1]).sum() / hours) if hours else np.nan,
           "awakenings_per_h": float(((s[1:] == "W") & (s[:-1] != "W")).sum() / hours) if hours else np.nan,
           "deepest": max(s, key=DEPTH.get) if len(s) else None, "sequence": "".join({"W": "W", "N1": "1", "N2": "2", "N3": "3"}[x] for x in s)}
    return out


def holm(p):
    p = np.asarray(p, float); order = np.argsort(p); adj = np.empty_like(p); run = 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (len(p) - i) * p[k])); adj[k] = run
    return adj


def friedman(wide):
    x = wide[SHORT].dropna()
    stat, p = friedmanchisquare(*[x[c] for c in SHORT])
    return {"n": len(x), "chi2": float(stat), "p": float(p), "kendall_w": float(stat / (len(x) * (len(SHORT) - 1))),
            "median": {c: float(x[c].median()) for c in SHORT}}


def adjacent(wide):
    x = wide[SHORT].dropna(); rows = []
    for a, b in zip(SHORT[:-1], SHORT[1:]):
        d = x[b] - x[a]
        p = float(wilcoxon(x[a], x[b]).pvalue) if (d != 0).any() else 1.0
        rows.append({"pair": f"{a} -> {b}", "median_change": float(d.median()), "higher": int((d > 0).sum()),
                     "lower": int((d < 0).sum()), "p": p})
    for r, a in zip(rows, holm([r["p"] for r in rows])):
        r["holm_p"] = float(a)
    return rows


def clusters(wide):
    x = wide[SHORT].dropna()
    z = linkage(x.to_numpy(), method="ward")
    sil = {k: float(silhouette_score(x, fcluster(z, k, "maxclust"))) for k in range(2, 6)}
    k = max(sil, key=sil.get)
    lab = pd.Series(fcluster(z, k, "maxclust"), index=x.index, name="cluster")
    order = x.mean(axis=1).groupby(lab).mean().sort_values().index          # cluster 1 = least sleep
    lab = lab.map({c: i + 1 for i, c in enumerate(order)})
    prof = x.groupby(lab).mean()
    return lab, {"silhouette": sil, "k": k, "profiles": {int(c): {r: float(v) for r, v in prof.loc[c].items()} for c in prof.index},
                 "sizes": {int(c): int(n) for c, n in lab.value_counts().sort_index().items()}}, z


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--group", choices=GROUPS, default="qualified"); a = ap.parse_args()
    out = HERE / "results" / GROUPS[a.group]; out.mkdir(parents=True, exist_ok=True)
    rows = []
    for sub in [f"{i:02d}" for i in range(1, 34)]:
        if (a.group != "all" and sub in EXCLUDED) or (a.group == "qualified" and sub not in SLEEPERS):
            continue
        lab = load_labels(sub)
        if not set(RUNS) <= set(lab.session):
            print(f"sub-{sub}: skipped (missing {sorted(set(RUNS) - set(lab.session))})"); continue
        rows += [{"subject": sub, **run_measures(lab, r)} for r in RUNS]
    d = pd.DataFrame(rows)
    piv = lambda m: d.pivot(index="subject", columns="run", values=m)[SHORT]
    ss = piv("sleep_share")
    rho = {s: float(spearmanr(range(5), ss.loc[s]).statistic) if ss.loc[s].nunique() > 1 else 0.0 for s in ss.index}
    d["person_rho"] = d.subject.map(rho)
    lab, cl, z = clusters(ss)
    d["cluster"] = d.subject.map(lab)
    d.to_csv(out / "per_run.csv", index=False)
    np.save(out / "linkage.npy", z)

    h1 = friedman(ss)
    page = page_trend_test(ss.dropna().to_numpy(), method="auto")
    sec = {m: friedman(piv(m)) for m in ("N2_share", "sleep_latency_s", "shifts_per_h")}
    for m, adj in zip(sec, holm([v["p"] for v in sec.values()])):
        sec[m]["holm_p"] = float(adj)
    follow = {"sleep_share": adjacent(ss)} if h1["p"] < 0.05 else {}
    follow.update({m: adjacent(piv(m)) for m, v in sec.items() if v["holm_p"] < 0.05})
    rest, sleep = ss[SHORT[:2]].mean(axis=1), ss[SHORT[2:]].mean(axis=1)
    trait = spearmanr(rest, sleep)
    summary = {
        "n": int(ss.shape[0]), "subjects": list(ss.index), "group": a.group,
        "H1_friedman_sleep_share": h1,
        "H2_page_trend": {"L": float(page.statistic), "p": float(page.pvalue), "method": page.method},
        "secondary": sec, "adjacent_pairs": follow,
        "trait_rest_vs_sleep": {"spearman_rho": float(trait.statistic), "p": float(trait.pvalue)},
        "slept_in_run": {r: int(d[d.run == r].slept.sum()) for r in SHORT},
        "n3_in_run": {r: int((d[d.run == r].N3_share > 0).sum()) for r in SHORT},
        "uncertain_epochs": int(d.n_uncertain.sum()),
        "person_direction": {"rising": int(sum(v > 0 for v in rho.values())), "falling": int(sum(v < 0 for v in rho.values())),
                             "flat": int(sum(v == 0 for v in rho.values()))},
        "clusters_exploratory": cl,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: summary[k] for k in ("n", "H1_friedman_sleep_share", "H2_page_trend", "secondary", "adjacent_pairs",
                                               "trait_rest_vs_sleep", "slept_in_run", "n3_in_run", "person_direction",
                                               "clusters_exploratory")}, indent=1))


if __name__ == "__main__":
    main()
