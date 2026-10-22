"""Exploratory "fully cleaned" arm (pre-registration amendment 1): stages 4b, 5 and 6 for every built participant.

For each recording, starting from the saved cleaned (MNE) recording:
  4b notch at 33.3 and 38.5 Hz -> 5 spherical-spline interpolation of PREP-bad channels -> 6 re-reference,
computed with BOTH candidate references (linked mastoids; average of all good channels).

Writes, per participant:
  data/features_full/sub-XX.csv     features for arms "full_mastoid" and "full_average" (same epochs,
                                    labels and quality flags as the main arms)
  data/features_full/refscore_sub-XX.csv   the amendment-1 reference-selection score for each reference
With --decide (after all participants are built): applies the pre-registered rule and writes
  studies/01-preprocessing-ablation/results/reference_choice.json

Usage:
  python studies/01-preprocessing-ablation/build_full_stages.py            # all built participants (skips done)
  python studies/01-preprocessing-ablation/build_full_stages.py --decide
"""
import argparse
import json
import sys
from pathlib import Path

import mne
import numpy as np
import pandas as pd
from scipy import signal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from features.spectral import epoch_features  # noqa: E402
from preprocessing import stages  # noqa: E402

CLEAN, QC, FEAT = ROOT / "data" / "clean", ROOT / "data" / "qc", ROOT / "data" / "features"
OUT = ROOT / "data" / "features_full"
RESULTS = Path(__file__).resolve().parent / "results"
POSTERIOR, CENTRAL = ["O1", "O2", "Pz"], ["C3", "C4", "Cz"]
REFS = {"full_mastoid": stages.linked_mastoids,
        "full_average": lambda r: r.copy().set_eeg_reference("average", verbose="error")}
EPOCH_S = 30
MAX_BAD_CHANNELS, MAX_BAD_EPOCH_PCT = 3, 25.0       # pre-registered exclusion rules


def band_power(raw, chans, lo, hi, starts):
    x = raw.get_data(picks=chans)
    sf = raw.info["sfreq"]
    vals = []
    for t in starts:
        seg = x[:, int(t * sf): int((t + EPOCH_S) * sf)]
        f, p = signal.welch(seg, fs=sf, nperseg=int(4 * sf), axis=-1)
        vals.append(p.mean(0)[(f >= lo) & (f < hi)].mean())
    return np.array(vals)


def process_participant(sub):
    main = pd.read_csv(FEAT / f"sub-{sub}.csv", dtype={"subject": str})
    epochs = main[main.arm == "cleaned_mne"][["subject", "session", "t", "stage", "qc_epoch_bad"]]
    qc = pd.read_csv(QC / f"sub-{sub}.csv", dtype={"subject": str}).set_index("session")
    rows, power = [], {k: {"W": [[], []], "N2": [[], []]} for k in REFS}   # [alpha, sigma] per stage
    for session, ep in epochs.groupby("session"):
        path = CLEAN / f"sub-{sub}_{session}_clean-mne_raw.fif"
        if not path.exists() or session not in qc.index:
            continue
        excluded_rec = qc.loc[session, "n_bad_channels"] > MAX_BAD_CHANNELS     # pre-registered rule 3
        raw = mne.io.read_raw_fif(path, preload=True, verbose="error")
        bads = [b for b in str(qc.loc[session, "bad_channels"]).split(";") if b and b != "nan"]
        base = stages.interpolate_bad(stages.notch_known_peaks(raw), bads)          # steps 4b and 5
        feat_ch = [c for c in raw.ch_names if c != "ECG"]
        for arm, ref in REFS.items():
            r = ref(base)                                                           # step 6
            x, sf = r.get_data(picks=feat_ch), r.info["sfreq"]
            for _, e in ep.iterrows():
                a = int(round(e.t * sf))
                rows.append({"subject": sub, "session": session, "t": e.t, "stage": e.stage, "arm": arm,
                             **epoch_features(x[:, a: a + int(EPOCH_S * sf)], sf, feat_ch),
                             "qc_epoch_bad": e.qc_epoch_bad})
            if excluded_rec:
                continue                                                        # features kept, not scored
            good = ep[~ep.qc_epoch_bad.astype(bool)]
            for st in ("W", "N2"):
                ts = good[good.stage == st].t.tolist()
                if ts:
                    power[arm][st][0] += band_power(r, POSTERIOR, 8, 12, ts).tolist()
                    power[arm][st][1] += band_power(r, CENTRAL, 12, 16, ts).tolist()
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / f"sub-{sub}.csv", index=False)
    score = []
    for arm in REFS:
        nw, nn = len(power[arm]["W"][0]), len(power[arm]["N2"][0])
        rec = {"subject": sub, "reference": arm, "n_wake": nw, "n_n2": nn}
        if nw >= 3 and nn >= 3:
            alpha = np.mean(power[arm]["W"][0]) / np.mean(power[arm]["N2"][0])
            sigma = np.mean(power[arm]["N2"][1]) / np.mean(power[arm]["W"][1])
            rec.update(alpha_contrast=alpha, spindle_contrast=sigma, score=np.log(alpha) + np.log(sigma))
        score.append(rec)
    pd.DataFrame(score).to_csv(OUT / f"refscore_sub-{sub}.csv", index=False)
    return pd.DataFrame(score)


def choose_reference(scores: pd.DataFrame) -> tuple[str, pd.Series]:
    """Amendment-1 rule: higher median score across participants; ties (< 0.01) go to the average reference."""
    s = scores.dropna(subset=["score"])
    med = s.groupby("reference").score.median()
    diff = med.get("full_mastoid", np.nan) - med.get("full_average", np.nan)
    return ("full_mastoid" if (not np.isnan(diff) and diff >= 0.01) else "full_average"), med


def excluded_people() -> set:
    """People excluded by pre-registered rule 4 (> 25% of epochs flagged by Autoreject)."""
    out = set()
    for f in QC.glob("sub-*.csv"):
        q = pd.read_csv(f, dtype={"subject": str})
        if 100 * q.n_bad_epochs.sum() / max(q.n_epochs.sum(), 1) > MAX_BAD_EPOCH_PCT:
            out.add(q.subject.iloc[0])
    return out


def decide():
    s = pd.concat([pd.read_csv(f, dtype={"subject": str}) for f in sorted(OUT.glob("refscore_sub-*.csv"))])
    s = s[~s.subject.isin(excluded_people())].dropna(subset=["score"])
    choice, med = choose_reference(s)
    out = {"rule": "pre-registration amendment 1: higher median score; ties (< 0.01) to average reference",
           "n_participants_scored": int(s.subject.nunique()),
           "median_score": med.round(4).to_dict(),
           "median_alpha_contrast": s.groupby("reference").alpha_contrast.median().round(3).to_dict(),
           "median_spindle_contrast": s.groupby("reference").spindle_contrast.median().round(3).to_dict(),
           "participants_spindle_contrast_above_1": s[s.spindle_contrast > 1].groupby("reference").subject.nunique().to_dict(),
           "choice": choice}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "reference_choice.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decide", action="store_true")
    args = ap.parse_args()
    if args.decide:
        return decide()
    for f in sorted(FEAT.glob("sub-*.csv")):
        sub = f.stem.split("-")[1]
        if (OUT / f"sub-{sub}.csv").exists():
            print(f"sub-{sub}: already done", flush=True)
            continue
        s = process_participant(sub)
        print(f"sub-{sub}: done; " + "; ".join(f"{r.reference}: score {r.score:.2f}" if pd.notna(getattr(r, "score", np.nan))
                                                else f"{r.reference}: not scorable (W {r.n_wake}, N2 {r.n_n2})"
                                                for r in s.itertuples()), flush=True)


if __name__ == "__main__":
    main()
