# Study 01: Does preprocessing matter?

EEG recorded during fMRI is buried under scanner and heartbeat artefacts hundreds of times larger than brain activity. Labs routinely remove them before analysis, but how much does that cleaning change what a sleep-staging model can learn?

This study answers that with an **ablation**: the same classifier, trained and tested on the same people and expert labels, using three versions of the same EEG.

| Arm | EEG used |
|---|---|
| **raw** | Straight from the dataset: 5 kHz, nothing removed or filtered |
| **filtered** | 0.3–40 Hz filter, 250 Hz, no artefact removal |
| **cleaned** | Scanner (gradient) and heartbeat (ballistocardiogram) artefacts removed, then the same filter |

## Data

All 33 participants of OpenNeuro ds003768: 6,858 cleanly labelled 30-second epochs (wake 3,343, N1 2,148, N2 1,325, N3 42). N3 is too rare to model and is merged with N2; epochs marked uncertain or unscorable (1.9%) are left out.

## Methods

1. **Scanner artefact:** average artefact subtraction locked to the R128 volume triggers, 21-volume sliding template (Allen, Josephs & Turner, 2000, *NeuroImage*).
2. **Heartbeat artefact:** R-peaks found in the ECG channel, then average artefact subtraction locked to each beat, 21-beat template (Allen et al., 1998, *NeuroImage*). Peak timing comes from the 8–25 Hz ECG energy; the minimum gap between beats is 0.6 × the interval given by MNE's heart-rate estimate, which prevents T-waves being counted as extra beats (the first version double-counted in some recordings, e.g. 106 bpm instead of 66 bpm for participant 4). Skipped for a recording if the heart rate is outside 40–120 bpm (logged).
3. **Filter and resample:** 0.3–40 Hz, 250 Hz.
4. **Features (identical for every arm):** per 30-second epoch and per region (frontal, central, posterior, temporal): log and relative power in delta, theta, alpha, sigma and beta, 95% spectral edge, theta/alpha ratio, Hjorth mobility and complexity; slow and fast eye-channel power. 67 features, plus a ±2-epoch context average. The ECG channel is never used as a feature.
5. **Quality checks and exclusions:** every recording is checked at four levels (below). Epochs flagged by Autoreject, recordings with more than 3 bad channels and people with more than 25% flagged epochs are excluded, judged on the cleaned recording and applied identically to all three arms.
6. **Tasks and models:** two tasks, wake / N1 / N2 and wake vs N2; two models, logistic regression on standardised features and gradient-boosted trees, both with balanced class weights. **Leave-one-person-out** cross-validation, so each person is scored by a model that never saw them.
7. **Statistics:** Cohen's kappa against the expert for each person; arms compared with paired Wilcoxon signed-rank tests and bootstrap 95% confidence intervals of the mean difference. A stratified-chance classifier gives the floor.

Steps 5–7 were revised on 22 Oct 2026, **before any 33-person results existed**, after a 4–5 person code test: logistic regression and the wake-vs-N2 task were added, and per-person feature scaling was dropped from the main analysis. People differ hugely in their mix of stages (one is 96% wake, another 76% N2), so scaling around each person's median removes stage information; it is kept as a sensitivity analysis (`--norm`).

## Results so far

Effect of cleaning on participant 1 (sleep run 1, 15 minutes; [`cleaning_effect.py`](cleaning_effect.py)):

| Measure | Uncleaned | Cleaned |
|---|---|---|
| Heartbeat artefact, O1, average of 1,229 beats | 86 µV peak-to-peak | 4 µV |
| Sleep-spindle band (sigma, 12–16 Hz) power, scalp mean | 23.5 µV²/Hz | 7.2 µV²/Hz (3.3× lower) |
| Beta band (16–30 Hz) power, scalp mean | 81.6 µV²/Hz | 1.3 µV²/Hz (62× lower) |

![Power spectrum before and after cleaning](../../figures/sub-01_task-sleep_run-1_psd.png)

Classifier comparison across all 33 people: **running**.

## Quality rules (set 22 Oct 2026, before the 33-person results)

Fixed in advance so cleaning is judged against criteria, not adjusted to the results. No universal published threshold exists for "acceptable power loss" in EEG-fMRI cleaning; rules 1–2 are this study's own criteria, based on the method's theoretical cost. Rules 3–4 follow common EEG-research conventions.

| # | Rule | Limit | How it's measured |
|---|---|---|---|
| 1 | **Brain signal lost to each artefact subtraction** | ≤ 5% of power in any band | Surrogate test: the same subtraction at random times ([`overcorrection_check.py`](overcorrection_check.py)) |
| 2 | **Residual heartbeat artefact** | Heartbeat-locked average no larger than averages locked to random times | Same script, extended to all participants |
| 3 | **Bad channels** | ≤ 10% of channels (3 of 30 scalp channels) per recording; more → recording excluded | PREP bad-channel detection |
| 4 | **Epochs rejected for artefact** | ≤ 25% of a person's epochs; more → person excluded from the main analysis and reported separately | Autoreject |

Every exclusion is listed in the results with its reason.

### How quality is checked

Every recording gets a quality record at four levels ([`src/preprocessing/quality.py`](../../src/preprocessing/quality.py)), summarised by [`src/postprocessing/quality_report.py`](../../src/postprocessing/quality_report.py):

| Level | Check | Tool / standard |
|---|---|---|
| 1. Files | Size and MD5 checksum match OpenNeuro's record; 32 channels at 5 kHz with ECG and EOG; regular scanner triggers | OpenNeuro / Amazon S3 checksums |
| 2. Channels | Flat, abnormal-amplitude, poorly correlated and unpredictable channels | PREP pipeline (Bigdely-Shamlo et al., 2015) via PyPREP; the high-frequency-noise criterion is not used because the data are low-passed at 40 Hz |
| 3. Epochs | A peak-to-peak rejection threshold learned from each recording; a 30-s epoch is flagged if 2 of its three 10-s windows exceed it | Autoreject (Jas et al., 2017) |
| 4. Correction | Rule 1 (surrogate brain-loss test), rule 2 (residual heartbeat vs random timing), residual slice-frequency peaks, heartbeat detection (40–120 bpm, no double counts, within 20 bpm of the person's median) | This study's checks |

First recording checked (participant 1, sleep run 1): checksum ✓, header ✓, 81 bpm with no double counts, brain loss 5.0% ✓, 1 bad channel (Fz, next to the recording reference) ✓, 4 of 30 epochs flagged (13%) ✓, **rule 2 ✗**: residual heartbeat 5.4 µV vs 4.3 µV for random timing. A small heartbeat residue remains after average artefact subtraction; this is reported, not re-thresholded, and motivates the planned optimal-basis-set step.

**Check of rule 1 on participant 1, sleep run 1:** heartbeat subtraction at real beat times removes 22–57% of band power; at random times it removes 3.3–5.1% (± 0.3–0.6 over 20 surrogates). So 79–92% of what it removes is artefact, and the brain-signal cost (3.3–5.1%) is within the 5% limit. A spindle-contrast check (sigma share in N2 vs wake) did not shrink after cleaning (ratio 0.67 → 0.70) but has only 3 wake epochs here and will be repeated across all participants.

## What does cleaning remove?

Measured on participant 1, sleep run 1, with [`data_accounting.py`](data_accounting.py):

| Step | What is removed | Share | Importance for sleep staging |
|---|---|---|---|
| Crop to scanning period | Seconds before the first and after the last scanner volume | 3.5% of recording time | None: these seconds have no sleep labels |
| Gradient subtraction | Scanner artefact | 99.68% of raw signal power | None: artefact; brain loss is about 1/21 (4.8%) of brain power, about 0.015% of raw power |
| 0.3–40 Hz filter | Slow drift below 0.3 Hz (10.5%) and activity above 40 Hz (2.3%) | 12.8% of remaining power | Low: sleep scoring uses 0.3–35 Hz; very slow brain activity and gamma are lost |
| Resample to 250 Hz | Samples that only describe frequencies above 125 Hz | 95% of samples | None after the 40 Hz filter |
| Heartbeat subtraction | Pulse artefact | 19.9% of filtered power: delta 22%, theta 31%, alpha 38%, sigma 57%, beta 34% | Mostly artefact (see below); about 4.8% of brain power goes with the template |
| Label tidying | Uncertain or unscorable epochs; N3 merged into N2 | 1.9% of epochs dropped; 0.6% relabelled | Deep sleep can't be studied as its own stage |

**Is the large sigma-band removal real artefact?** Heartbeat removal with MNE's standard R-peak detector keeps more sigma-band power (14.4 vs 7.1 µV²/Hz), but its beat times scatter by up to 28 ms, and checked against precise beat times it leaves 42 µV of heartbeat artefact versus 5.5 µV for ours. The extra power is residual artefact, not preserved brain signal.

## Is brain signal preserved?

[`signal_preservation.py`](signal_preservation.py) compares the cleaned scanning period with the 24 seconds recorded before the first scanner volume. Between 0.5 and 15 Hz both have the same shape, including the alpha peak near 10 Hz and a spindle-range peak near 13 Hz, so cleaning keeps the brain rhythms sleep staging relies on.

![Pre-scan vs cleaned scanning spectrum](results/signal_preservation_sub-01.png)

The check also showed:

- The pre-scan stretch already contains the 16.7 Hz slice rhythm, so the scanner was running unmarked warm-up volumes. It is a useful but imperfect reference.
- The 38.5 Hz peak is present before scanning too: it comes from other scanner-room equipment, not from incomplete gradient removal, and needs a targeted notch filter.
- Peaks at about 3 and 6 Hz appear only during scanning and may be residual artefact; to investigate.
- The first R-peak detector found only 7 of 32 beats in the pre-scan stretch. The cause is the unmarked warm-up volumes: their 16.7 Hz slice artefact falls inside the detector's 8–25 Hz band. This comparison therefore used MNE's detector, which leaves residual heartbeat artefact, so its sigma and beta bands are inflated on both sides. To be redone.

## Limitations

- Narrow residual artefact peaks between 20 and 48 Hz remain after cleaning (visible in the spectrum above).
- The artefact templates include the current volume or heartbeat, which subtracts about 1/21 (5%) of that segment's own brain signal; excluding it is a planned refinement.
- Cleaning removes any brain response genuinely locked to the heartbeat (heartbeat-evoked potentials, a few µV). This doesn't affect sleep staging but would matter for research on body–brain signals.
- Naps in a scanner contain almost no deep sleep, and only 16 of 33 people have 10 or more minutes of N2.
- 33 people is a small sample; results are reported per person with confidence intervals, not only as one pooled number.

## Reproduce

```bash
python studies/01-preprocessing-ablation/build_dataset.py     # download, clean, quality-check, extract features (~9 h)
python src/postprocessing/quality_report.py studies/01-preprocessing-ablation/results   # quality tables + figure
python studies/01-preprocessing-ablation/compare_arms.py      # leave-one-person-out comparison -> results/
python studies/01-preprocessing-ablation/cleaning_effect.py <recording.vhdr>
```
