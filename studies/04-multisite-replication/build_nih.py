"""Study 04: build study 01's feature table for NIH ds005127 (overnight EEG-fMRI), one participant at a time.

Same arms, cleaning and features as studies/01-preprocessing-ablation/build_dataset.py. Differences are practical:
runs are 30-60 min of 65 channels at 5 kHz, so each run is processed one channel at a time (memory), downloaded
one run at a time and its .eeg deleted after use (disk). Labels come from derivatives/sleep_scoring_mr (30-s
epochs from the start of the EEG file; the dataset FAQ's codebook).

Live progress is written to data/status/nih.json (read by notes/pipeline_tracker.py).

Usage:
    python studies/04-multisite-replication/build_nih.py --subjects 00002 00067 --budget-min 60
"""
from __future__ import annotations

import argparse
import gc
import json
import re
import sys
import threading
import time
import urllib.request
from pathlib import Path

import mne
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "studies" / "01-preprocessing-ablation"))
from build_dataset import s3_list, to_250                                       # noqa: E402
from features.spectral import epoch_features                                    # noqa: E402
from preprocessing import quality                                               # noqa: E402
from preprocessing.mr_artifacts import (TARGET_SFREQ, heart_rate_mne, r_peaks, r_peaks_mne,  # noqa: E402
                                        remove_bcg, remove_gradient, volume_onsets)

DS = "ds005127"
S3 = "https://s3.amazonaws.com/openneuro.org"
EXT = ROOT / "data" / "external" / DS
OUT = ROOT / "data" / "features_nih"
QC = ROOT / "data" / "qc_nih"
CLEAN = ROOT / "data" / "clean_nih"
STATUS = ROOT / "data" / "status" / "nih.json"
EPOCH_S = 30
# dataset FAQ: (Score, REM) -> stage; N3 merged into N2 for staging as in study 01, REM kept for description only
CODE = {(6, 0): "W", (4, 0): "N1", (3, 0): "N2", (2, 0): "N3", (1, 0): "N3", (4, 1): "R", (0, 0): None}
STAGING = {"W": "W", "N1": "N1", "N2": "N2", "N3": "N2"}
DROP = ("E2", "EMG")                     # second eye channel and chin EMG: not used (E1 is the EOG channel)
SAVE_CH = ["F3", "F4", "C3", "C4", "O1", "O2", "TP9", "TP10", "ECG", "EOG"]   # kept for event detection (H4)
STAGES = ["download", "labels + triggers", "raw arm", "filtered + scanner artefact", "filtered arm", "heartbeat (MNE)",
          "heartbeat (refined)", "quality checks", "save"]   # order shown by the tracker


class Status:
    """Writes the tracker's JSON; every update is atomic so the tracker never reads half a file."""

    def __init__(self, subjects, budget_min):
        self.s = {"dataset": DS, "started": time.time(), "budget_min": budget_min, "subjects": subjects,
                  "done_subjects": [], "outcomes": [], "log": [], "current": None, "prefetch": None}
        self.lock = threading.Lock()
        STATUS.parent.mkdir(parents=True, exist_ok=True)

    def set(self, **kw):
        with self.lock:
            cur = self.s["current"] or {}
            cur.update(kw); cur["updated"] = time.time(); self.s["current"] = cur
        self.flush()

    def set_prefetch(self, **kw):
        with self.lock:
            self.s["prefetch"] = {**(self.s["prefetch"] or {}), **kw, "updated": time.time()} if kw else None
        self.flush()

    def log(self, msg):
        with self.lock:
            self.s["log"] = (self.s["log"] + [f"{time.strftime('%H:%M:%S')}  {msg}"])[-40:]
        self.flush()
        print(msg, flush=True)

    def flush(self):
        """Best effort: the tracker may hold the file for a moment (Windows locks it); never let that stop the run."""
        with self.lock:
            text = json.dumps(self.s, default=float)
        tmp = STATUS.with_suffix(f".{threading.get_ident()}.tmp")
        for _ in range(10):
            try:
                tmp.write_text(text); tmp.replace(STATUS); return
            except OSError:
                time.sleep(0.05)
        tmp.unlink(missing_ok=True)


def download(key, st: Status, prefetch=False, tries=5):
    dest = EXT / key.removeprefix(f"{DS}/")
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(f"{S3}/{key}", timeout=60) as r, open(tmp, "wb") as f:
                total, got, t0 = int(r.headers.get("Content-Length", 0)), 0, time.time()
                while chunk := r.read(1 << 22):
                    f.write(chunk); got += len(chunk)
                    if total > 50e6:
                        prog = dict(pct=got / total, detail=f"{got / 1e9:.2f} / {total / 1e9:.2f} GB",
                                    mb_s=got / 1e6 / max(time.time() - t0, 1e-3))
                        if prefetch:
                            st.set_prefetch(file=dest.name, **prog)
                        else:
                            st.set(stage="download", stage_pct=prog["pct"], detail=prog["detail"], mb_s=prog["mb_s"])
            tmp.replace(dest)
            with st.lock:
                st.s["downloaded_gb"] = st.s.get("downloaded_gb", 0) + got / 1e9
            return dest
        except OSError as e:
            tmp.unlink(missing_ok=True)
            if attempt == tries:
                raise
            st.log(f"download retry {attempt}: {dest.name}: {e}"); time.sleep(10 * attempt)


def labels_for(base: str) -> pd.DataFrame:
    """Expert scores for one run: row k is the 30-s epoch starting k*30 s after the EEG file starts."""
    sub, ses = base.split("/")[1], base.split("/")[2]
    name = Path(base).name.removesuffix("_eeg")
    d = pd.read_csv(EXT / "derivatives" / "sleep_scoring_mr" / sub / ses / f"{name}.txt", sep="\t")
    d["t_file"] = np.arange(len(d)) * EPOCH_S
    d["stage_full"] = [CODE.get((int(s), int(r)), None) for s, r in zip(d.Score, d.REM)]
    d["stage"] = d.stage_full.map(STAGING)                                        # REM, unscorable -> NaN
    return d


def channel_major(raw, eeg_path: Path, st: Status, chunk=1_000_000):
    """Rewrite the multiplexed int16 file channel by channel (one sequential pass), so each channel can be read
    without re-reading the whole file. Scaling per channel is taken from MNE's own reader and checked."""
    hdr = Path(raw.filenames[0]).with_suffix(".vhdr").read_text(encoding="latin-1")
    assert "DataOrientation=MULTIPLEXED" in hdr and "BinaryFormat=INT_16" in hdr, "unexpected BrainVision layout"
    n_file = int(re.search(r"^NumberOfChannels=(\d+)", hdr, flags=re.M).group(1))
    src = np.memmap(eeg_path, np.int16, "r").reshape(-1, n_file)
    dst_path = eeg_path.with_suffix(".chmajor")
    dst = np.memmap(dst_path, np.int16, "w+", shape=(n_file, src.shape[0]))
    for i in range(0, src.shape[0], chunk):
        dst[:, i:i + chunk] = src[i:i + chunk].T
        st.set(stage="labels + triggers", stage_pct=min(i / src.shape[0], 1), detail="re-ordering the file by channel")
    dst.flush()
    return dst, dst_path


def process_run(base: str, sub: str, st: Status):
    """One run: same arms as study 01, one channel at a time. Returns feature rows, run QC, stage counts."""
    files = {ext: download(f"{base}.{ext}", st) for ext in ("vhdr", "vmrk", "json", "eeg")}
    st.set(stage="labels + triggers", stage_pct=0, detail="reading header, scanner triggers and expert scores")
    raw = mne.io.read_raw_brainvision(files["vhdr"], preload=False, verbose="error")
    file_idx = {("EOG" if c == "E1" else c): i for i, c in enumerate(raw.ch_names)}   # position in the data file
    raw.drop_channels([c for c in DROP if c in raw.ch_names]).rename_channels({"E1": "EOG"})
    sf, names = raw.info["sfreq"], raw.ch_names
    qc = {"subject": sub, "run": Path(base).name, "n_channels": len(names), "sfreq": sf}
    qc.update(quality.file_check(files["eeg"], f"{S3}/{base}.eeg"))
    side = json.loads(files["json"].read_text())
    onsets = volume_onsets(raw)
    tr = np.diff(onsets) / sf
    qc.update(n_volumes=len(onsets), tr_s=float(np.median(tr)) if len(tr) else np.nan,
              tr_irregular=int(np.sum(np.abs(tr - np.median(tr)) > 0.01)) if len(tr) else -1,
              sidecar_sfreq_matches=side.get("SamplingFrequency") == sf)
    lab = labels_for(base)
    counts = lab.stage_full.fillna("unscorable").value_counts().to_dict()
    if len(onsets) < 50:
        qc["status"] = "skipped: too few scanner triggers"; return [], qc, counts
    seg = int(np.median(np.diff(onsets)))                                        # one TR (see remove_gradient)
    qc["triggers_irregular"] = int(np.sum(np.diff(onsets) != seg))
    span = slice(int(onsets[0]), int(onsets[-1] + seg))
    on = onsets - span.start
    inside = (lab.t_file * sf >= span.start) & ((lab.t_file + EPOCH_S) * sf <= span.stop)
    lab = lab[inside & (lab.MRIon >= 1) & lab.stage.notna()].copy()
    lab["t"] = lab.t_file - span.start / sf                                      # seconds from scan start
    qc.update(n_scored_epochs_in_scan=len(lab), label_rows=len(inside), eeg_epochs=int(raw.n_times / sf // EPOCH_S))
    if lab.empty:
        qc["status"] = "skipped: no scored epochs with the scanner on"; return [], qc, counts
    feat_ch = [c for c in names if c != "ECG"]
    rows = []

    def add(arm, get_seg, rate):
        for i, (_, e) in enumerate(lab.iterrows()):
            a = int(round(e.t * rate))
            rows.append({"subject": sub, "run": Path(base).name, "t": e.t, "t_file": e.t_file, "stage": e.stage,
                         "arm": arm, **epoch_features(get_seg(a, a + int(EPOCH_S * rate)), rate, feat_ch)})

    # A: raw, 5 kHz, read epoch by epoch straight from the file
    st.set(stage="raw arm", stage_pct=0, detail=f"{len(lab)} epochs at 5 kHz")
    fi = [names.index(c) for c in feat_ch]
    add("raw", lambda a, b, r=raw: r.get_data(picks=fi, start=span.start + a, stop=span.start + b), sf)
    # B and the scanner-cleaned signal, one channel at a time (memory: ~0.1 GB per channel at 5 kHz)
    cm, cm_path = channel_major(raw, files["eeg"], st)
    probe = raw.get_data(start=span.start, stop=span.start + 5000)               # MNE's scaling (volts per unit)
    scale = {}
    for k, ch in enumerate(names):
        units = cm[file_idx[ch], span.start:span.start + 5000].astype(float)
        nz = units != 0
        scale[ch] = float(np.median(probe[k][nz] / units[nz])) if nz.any() else 0.0
        assert np.allclose(probe[k], units * scale[ch], atol=1e-9), f"scaling check failed for {ch}"
    filt, grad = [], []
    for k, ch in enumerate(names):
        st.set(stage="filtered + scanner artefact", stage_pct=k / len(names),
               detail=f"channel {k + 1}/{len(names)} ({ch}): filter + 250 Hz; average artefact subtraction + 250 Hz")
        x = cm[file_idx[ch], span.start:span.stop].astype(np.float64)[None] * scale[ch]
        info1 = mne.create_info([ch], sf, "ecg" if ch == "ECG" else "eog" if ch == "EOG" else "eeg")
        filt.append(to_250(x, info1, slice(None))[0])
        remove_gradient(x, on)
        grad.append(to_250(x, info1, slice(None))[0])
    del cm; gc.collect(); cm_path.unlink(missing_ok=True)
    n = min(len(v) for v in filt + grad)
    filt = np.array([v[:n] for v in filt]); grad = np.array([v[:n] for v in grad])
    st.set(stage="filtered arm", stage_pct=1, detail="features")
    add("filtered", lambda a, b, f=filt: f[fi, a:b], TARGET_SFREQ)
    del filt
    ecg = grad[names.index("ECG")]
    scalp = [i for i, c in enumerate(names) if c not in ("ECG", "EOG")]
    before = grad[scalp].copy()
    ref_hz = heart_rate_mne(ecg, TARGET_SFREQ) / 60.0
    info250 = mne.create_info(names, TARGET_SFREQ, ["ecg" if c == "ECG" else "eog" if c == "EOG" else "eeg" for c in names])
    cleaned = {}
    for arm, detector, label in (("cleaned_mne", r_peaks_mne, "heartbeat (MNE)"), ("cleaned_refined", r_peaks, "heartbeat (refined)")):
        st.set(stage=label, stage_pct=0, detail="R-peak detection, average artefact subtraction, features")
        x = grad.copy(); peaks = detector(ecg, TARGET_SFREQ)
        stats = quality.heartbeat_detection_stats(peaks, TARGET_SFREQ); tag = arm.split("_")[1]
        qc.update({f"{k}_{tag}": v for k, v in stats.items()})
        if 40 <= stats["heart_rate_bpm"] <= 120:
            s = x[scalp]; remove_bcg(s, peaks, TARGET_SFREQ); x[scalp] = s
            qc[f"inps_db_{tag}"] = quality.inps_db(before, s, ref_hz, TARGET_SFREQ)
        else:
            qc[f"bcg_{tag}"] = "skipped: implausible heart rate"
        add(arm, lambda a, b, x=x: x[fi, a:b], TARGET_SFREQ)
        cleaned[arm] = x
    del grad, before
    st.set(stage="quality checks", stage_pct=0, detail="PREP bad channels (deviation, correlation, RANSAC)")
    std = mne.io.RawArray(cleaned["cleaned_mne"].astype(np.float32), info250, verbose="error")
    qc.update(quality.channel_check(std))
    bad_ch = [c for c in qc["bad_channels"].split(";") if c]
    qc["n_scalp_channels"] = len(scalp)
    st.set(stage="quality checks", stage_pct=0.5, detail="Autoreject epoch threshold")
    ep, flags = quality.epoch_check(std, lab.t.tolist(), bad_ch)
    qc.update(ep)
    bad_at = dict(zip(lab.t.tolist(), flags))
    for r in rows:
        r["qc_epoch_bad"] = bad_at[r["t"]]
    st.set(stage="save", stage_pct=0, detail="detector channels for event analysis")
    CLEAN.mkdir(parents=True, exist_ok=True)
    keep = [c for c in SAVE_CH if c in names]
    std.copy().pick(keep).save(CLEAN / f"{Path(base).name}_clean-mne_raw.fif", overwrite=True, verbose="error")
    qc["status"] = "ok"
    raw.close(); del raw, std, cleaned
    return rows, qc, counts


def run_subject(sub: str, st: Status, keep_raw=False):
    keys = s3_list(f"{DS}/sub-{sub}/")
    runs = sorted({k.removesuffix(".eeg") for k in keys if "/eeg/" in k and k.endswith("_eeg.eeg") and "task-sleep" in k})
    rows, qcs, counts = [], [], {}
    t_sub = time.time()
    fetcher = None

    def prefetch(b):                                                  # next run downloads while this one is processed
        try:
            for ext in ("vhdr", "vmrk", "json", "eeg"):
                download(f"{b}.{ext}", st, prefetch=True)
        except Exception as e:                                          # the main loop downloads it again if needed
            st.log(f"prefetch failed for {Path(b).name}: {e}")
        st.set_prefetch()

    for i, base in enumerate(runs, 1):
        if fetcher is not None:
            st.set(subject=sub, run_i=i, run_n=len(runs), run=Path(base).name, stage="download", stage_pct=0,
                   detail="waiting for the background download of this run")
            fetcher.join()                                              # never two writers on the same file
        st.set(subject=sub, run_i=i, run_n=len(runs), run=Path(base).name, run_started=time.time(), stage="download", stage_pct=0)
        if i < len(runs):
            fetcher = threading.Thread(target=prefetch, args=(runs[i],), daemon=True)
            for ext in ("vhdr", "vmrk", "json", "eeg"):                 # current run first, then start the prefetch
                download(f"{base}.{ext}", st)
            fetcher.start()
        t0 = time.time()
        try:
            r, qc, c = process_run(base, sub, st)
        except Exception as e:                                                     # keep going; record the failure
            r, qc, c = [], {"subject": sub, "run": Path(base).name, "status": f"error: {type(e).__name__}: {e}"}, {}
        qc["seconds"] = round(time.time() - t0)
        rows += r; qcs.append(qc)
        for k, v in c.items():
            counts[k] = counts.get(k, 0) + v
        st.log(f"sub-{sub} run {i}/{len(runs)}: {qc.get('status')} · epochs {qc.get('n_epochs', 0)} "
               f"(bad {qc.get('n_bad_epochs')}) · bad ch {qc.get('n_bad_channels')} · HR {qc.get('heart_rate_bpm_mne', float('nan')):.0f} "
               f"· INPS {qc.get('inps_db_mne', float('nan')):.1f} dB · {qc['seconds']} s")
        st.s.setdefault("run_seconds", []).append(qc["seconds"]); st.flush()
        gc.collect()                                                              # release memory-mapped file handles
        local = EXT / base.removeprefix(f"{DS}/")                                 # same path download() wrote to
        for path in [local.with_suffix(".chmajor")] + ([] if keep_raw else [local.with_suffix(".eeg")]):
            for _ in range(5):
                try:
                    path.unlink(missing_ok=True); break
                except PermissionError:
                    time.sleep(2); gc.collect()
            else:
                st.log(f"could not delete {path.name} (still in use); delete it manually")
    OUT.mkdir(parents=True, exist_ok=True); QC.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / f"sub-{sub}.csv", index=False)
    q = pd.DataFrame(qcs); q.to_csv(QC / f"sub-{sub}.csv", index=False)
    ok = q[q.status == "ok"] if "status" in q else q.iloc[:0]
    feats = pd.DataFrame(rows)
    one = feats[feats.arm == "cleaned_mne"] if len(feats) else feats
    pct_bad = float(100 * one.qc_epoch_bad.mean()) if len(one) else float("nan")
    rule4 = [f"{r}: {b}/{s}" for r, b, s in zip(ok.run, ok.n_bad_channels, ok.n_scalp_channels) if b > 0.10 * s]
    outcome = {"subject": sub, "minutes": round((time.time() - t_sub) / 60, 1), "runs": len(runs), "runs_ok": len(ok),
               "scored_epochs_all": counts, "epochs_analysed": int(len(one)),
               "stages_analysed": one.stage.value_counts().to_dict() if len(one) else {},
               "pct_bad_epochs": round(pct_bad, 1), "rule5_excluded": bool(pct_bad > 25),
               "runs_rule4_excluded": rule4,
               "bad_channels_median": float(ok.n_bad_channels.median()) if len(ok) else None,
               "heart_rate_median": float(ok.heart_rate_bpm_mne.median()) if len(ok) else None,
               "inps_db_mne_median": float(ok.inps_db_mne.median()) if "inps_db_mne" in ok and len(ok) else None,
               "inps_db_refined_median": float(ok.inps_db_refined.median()) if "inps_db_refined" in ok and len(ok) else None,
               "double_counts_mne": int(ok.double_counts_mne.sum()) if len(ok) else None,
               "md5_ok": bool(ok.file_md5_ok.fillna(True).all()) if len(ok) else None,
               "errors": [f"{r}: {s}" for r, s in zip(q.run, q.status) if not str(s).startswith(("ok", "skipped"))]}
    st.s["outcomes"].append(outcome); st.s["done_subjects"].append(sub); st.flush()
    st.log(f"sub-{sub} DONE in {outcome['minutes']} min: {outcome['epochs_analysed']} epochs, "
           f"{outcome['pct_bad_epochs']}% rejected, rule 5 {'FAIL' if outcome['rule5_excluded'] else 'pass'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="+", required=True)
    ap.add_argument("--budget-min", type=float, default=60, help="start no new participant after this many minutes")
    ap.add_argument("--keep-raw", action="store_true")
    a = ap.parse_args()
    st = Status(a.subjects, a.budget_min)
    st.log(f"pilot started: {', '.join(a.subjects)} (budget {a.budget_min:.0f} min)")
    for sub in a.subjects:
        if (time.time() - st.s["started"]) / 60 > a.budget_min:
            st.log(f"time budget reached: stopping before sub-{sub}"); break
        if (OUT / f"sub-{sub}.csv").exists():
            st.log(f"sub-{sub}: already done"); continue
        run_subject(sub, st, a.keep_raw)
    st.s["current"] = None; st.s["finished"] = time.time(); st.log("pilot finished")


if __name__ == "__main__":
    main()
