"""Build the nap-report page (sleep-app view + research view) for every participant built so far.

Reads saved outputs only: expert labels, data/features (raw and cleaned band power, quality flags),
data/qc, data/features_events (refined-arm slow waves and spindles), the cleaned recordings (ECG heart
rate per epoch) and the participant table (within-person staging kappa). Participant 1's exploratory
OBS staging results are added when present.

Usage: python src/postprocessing/nap_report.py [template.html] [out.html]
Defaults: src/postprocessing/nap_report_template.html -> data/report/nap-report.html
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "studies" / "01-preprocessing-ablation"
sys.path.insert(0, str(STUDY))
sys.path.insert(0, str(ROOT / "src"))
import hr_check  # noqa: E402
from build_dataset import load_labels  # noqa: E402

DATA = ROOT / "data"
STAGE = {"W": "W", "1": "N1", "2": "N2", "3": "N3"}
BANDS = {"alpha": "posterior_rel_alpha", "sigma": "central_rel_sigma", "delta": "frontal_rel_delta"}


def r1(x, d=1):
    return None if x is None or pd.isna(x) else round(float(x), d)


def participant(sub, table):
    f = pd.read_csv(DATA / "features" / f"sub-{sub}.csv", dtype={"subject": str})
    labels = load_labels(sub)
    ep = f[f.arm == "cleaned_mne"][["subject", "session", "t", "qc_epoch_bad"]].reset_index(drop=True)
    ep = ep.merge(labels[["session", "t", "stage_raw"]], on=["session", "t"], how="left")
    ep["s"] = ep.stage_raw.map(STAGE)                               # N3 kept separate here (merged into N2 in the study)
    ep = ep.merge(hr_check.heart_rates(ep[["subject", "session", "t"]]), on=["subject", "session", "t"], how="left")
    evf = DATA / "features_events" / f"sub-{sub}.csv"
    if evf.exists():
        ev = pd.read_csv(evf)
        ep = ep.merge(ev[ev.arm == "cleaned_refined"][["session", "t", "sw_density", "sp_density"]], on=["session", "t"], how="left")
    else:
        ep["sw_density"] = ep["sp_density"] = np.nan
    bands = {arm: f[f.arm == arm].set_index(["session", "t"])[list(BANDS.values())] for arm in ("raw", "cleaned_mne")}
    q = pd.read_csv(DATA / "qc" / f"sub-{sub}.csv").set_index("session")
    recs = []
    for ses, g in ep.groupby("session", sort=False):
        g = g.sort_values("t")
        st = g.s.tolist()
        onset = next((i for i, x in enumerate(st) if x != "W"), None)
        x = q.loc[ses]
        recs.append({
            "id": ses, "kind": "rest" if "rest" in ses else "sleep", "run": int(ses.split("-")[-1]),
            "minutes": len(st) / 2, "latency_min": None if onset is None else onset / 2,
            "tst_min": sum(s != "W" for s in st) / 2,
            "waso_min": 0 if onset is None else sum(s == "W" for s in st[onset:]) / 2,
            "awakenings": 0 if onset is None else sum(1 for i in range(max(onset, 1), len(st)) if st[i] == "W" and st[i - 1] != "W"),
            "hr_bpm": r1(x.heart_rate_bpm_mne),
            "qc": {"inps_mne": r1(x.inps_db_mne, 2), "inps_ref": r1(x.inps_db_refined, 2), "md5": bool(x.file_md5_ok),
                   "bad_ch": "" if pd.isna(x.bad_channels) else str(x.bad_channels), "volumes": int(x.n_volumes),
                   "dbl_mne": int(x.double_counts_mne), "dbl_ref": int(x.double_counts_refined), "tr": r1(x.tr_s, 2)},
            "epochs": [{"t": float(e.t), "s": e.s, "bad": bool(e.qc_epoch_bad), "hr": r1(e.hr),
                        "sw": r1(e.sw_density, 2), "sp": r1(e.sp_density, 2),
                        "raw": {k: r1(bands["raw"].loc[(ses, e.t), c], 4) for k, c in BANDS.items()},
                        "cln": {k: r1(bands["cleaned_mne"].loc[(ses, e.t), c], 4) for k, c in BANDS.items()}}
                       for e in g.itertuples()],
        })
    t = table.loc[sub]
    staging = [{"task": task, "model": "logreg", "arm": arm, "kappa": r1(t[f"within_{task}_{arm}"], 3)}
               for task in ("w_vs_n2", "3class") for arm in ("raw", "filtered", "cleaned_mne", "cleaned_refined")]
    obs = STUDY / "results" / f"obs_staging_sub-{sub}.csv"
    if obs.exists():                                                 # exploratory OBS arms and the second model
        s = pd.read_csv(obs)
        staging = [{"task": r.task, "model": r.model, "arm": r.arm, "kappa": r1(r.kappa, 3)} for r in s.itertuples()]
    skipped = q[q.status != "ok"]
    return {"participant": sub, "status": str(t.status), "flagged_pct": r1(t.flagged_pct),
            "skipped": [{"id": i, "why": str(r.status)} for i, r in skipped.iterrows()],
            "hr_by_stage": {k: r1(v) for k, v in ep.groupby("s").hr.mean().items()},
            "recordings": [r for r in recs if r["id"] in set(q[q.status == "ok"].index)], "staging": staging}


def main():
    template = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("nap_report_template.html")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else DATA / "report" / "nap-report.html"
    table = pd.read_csv(STUDY / "results" / "participants_table.csv", dtype={"participant": str}).set_index("participant")
    done = sorted(p.stem.split("-")[1] for p in (DATA / "features_events").glob("sub-*.csv"))
    people = []
    for sub in done:
        if sub in table.index and (DATA / "qc" / f"sub-{sub}.csv").exists():
            people.append(participant(sub, table))
            print(f"sub-{sub}: {sum(len(r['epochs']) for r in people[-1]['recordings'])} epochs", flush=True)
    payload = {"people": people, "dataset": {"n_people": 33, "n3_minutes": 21.0}}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(template.read_text(encoding="utf-8").replace("__DATA__", json.dumps(payload, separators=(",", ":"))), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(people)} participants)")


if __name__ == "__main__":
    main()
