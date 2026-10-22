# Study 01: Does preprocessing matter?

EEG recorded during fMRI is buried under scanner and heartbeat artefacts hundreds of times larger than brain activity. Labs routinely remove them before analysis, but how much does that cleaning change what a sleep-staging model can learn, and how much does the choice of heartbeat detector matter?

This study answers that with an **ablation**: the same classifier, trained and tested on the same people and expert labels, using four versions of the same EEG.

| Arm | EEG used |
|---|---|
| **raw** | Straight from the dataset: 5 kHz, nothing removed or filtered |
| **filtered** | 0.3–40 Hz filter, 250 Hz, no artefact removal |
| **cleaned (MNE)** | Scanner and heartbeat artefacts removed, then the same filter. Heartbeats found by MNE-Python's standard ECG detector, unmodified |
| **cleaned (refined)** | The same, with each detected beat aligned to its ECG peak (one beat per interval) |

## Data

All 33 participants of OpenNeuro ds003768: 6,858 cleanly labelled 30-second epochs (wake 3,343, N1 2,148, N2 1,325, N3 42). N3 is too rare to model and is merged with N2. Epochs the dataset's expert scorer marked **uncertain or unscorable** (1.9%) are left out, using the study's own flags.

## Methods

Only established EEG methods and the dataset's own information are used for cleaning and scoring.

1. **Scanner artefact:** average artefact subtraction locked to the R128 volume triggers, 21-volume sliding template (Allen, Josephs & Turner, 2000, *NeuroImage*).
2. **Heartbeat artefact:** average artefact subtraction locked to each heartbeat, 21-beat template (Allen et al., 1998, *NeuroImage*). Two detectors, compared as arms: MNE-Python's `find_ecg_events`, unmodified; and the same with timing refinement (beat placed at the 8–25 Hz ECG energy peak, at most one per 0.6 beat intervals). The refinement is this study's documented adaptation, not a published detector. Removal is skipped if the heart rate is outside 40–120 bpm (logged).
3. **Filter and resample:** 0.3–40 Hz, 250 Hz.
4. **Features (identical for every arm):** per 30-second epoch and per region (frontal, central, posterior, temporal): log and relative power in delta, theta, alpha, sigma and beta, 95% spectral edge, theta/alpha ratio, Hjorth mobility and complexity; slow and fast eye-channel power. 67 features, plus a ±2-epoch context average. The ECG channel is never used as a feature.
5. **Quality checks and exclusions:** see below. Judged on the standard-cleaned (MNE) recording and applied identically to every arm.
6. **Tasks and models:** wake / N1 / N2 and wake vs N2; logistic regression on standardised features and gradient-boosted trees, both with balanced class weights. **Leave-one-person-out** cross-validation.
7. **Statistics:** Cohen's kappa against the expert for each person; arms compared with paired Wilcoxon signed-rank tests and bootstrap 95% confidence intervals of the mean difference; a stratified-chance classifier gives the floor.

## Quality checks (established methods only)

Every recording is checked at four levels ([`src/preprocessing/quality.py`](../../src/preprocessing/quality.py); summary by [`src/postprocessing/quality_report.py`](../../src/postprocessing/quality_report.py)):

| Level | What is checked | Method | Used for |
|---|---|---|---|
| 1. Files | Size and MD5 checksum against OpenNeuro; 32 channels, ECG and EOG, regular scanner triggers; agreement with the dataset's BIDS metadata | Checksums; BIDS sidecar files | Pass/fail |
| 2. Channels | Flat, abnormal-amplitude, poorly correlated and unpredictable channels | **PREP** (Bigdely-Shamlo et al., 2015) via PyPREP. Its high-frequency-noise criterion is not used: the data are low-passed at 40 Hz | Recording excluded if > 3 of 30 channels are bad (10%, a common convention) |
| 3. Epochs | Epochs whose peak-to-peak amplitude exceeds a threshold learned from the recording | **Autoreject** global threshold (Jas et al., 2017), on the labelled 30-s epochs | Epoch excluded; person excluded if > 25% flagged (a common convention) |
| 4. Correction | Heartbeat removal: **INPS**, summed power in 1-Hz windows at the first five heart-rate harmonics before vs after, in dB (Tong et al., 2001, *J. Neurosci. Methods*). Scanner removal: residual peak at the slice frequency and its harmonic | Published metrics | Reported per recording and per detector; no pass/fail, because no published threshold exists |

Signal preservation is checked with the dataset's own labels: for each person, posterior alpha should be higher in wake than in N2 (the standard alpha contrast, here across sleep stages). Reported for every arm.

**What the checks found so far:**

- **Metadata mismatch:** the dataset's BIDS metadata says the EEG is sampled at 250 Hz, but every file header and the data itself are 5,000 Hz. Recorded as an integrity finding; the files are used as they are.
- **Recording reference FCz** (from the metadata) explains why Fz and Cz look nearly flat and why PREP flags them.
- **General-purpose ECG detectors fail on in-scanner ECG** ([`compare_qrs_detectors.py`](compare_qrs_detectors.py)). On participants 1 and 4, NeuroKit2's published clinical detectors (Pan–Tompkins, Hamilton, Elgendi, Engzee, Christov) and a Teager-energy detector reported 110–254 bpm or missed or double-counted hundreds of beats. MNE's detector found the right rate (82 and 66 bpm) but double-counted 87 and 155 beats (7–14%). The refined version counted none double, with INPS 1.64 vs 0.99 dB and 1.21 vs 1.17 dB.

## Results so far

Effect of cleaning on participant 1 (sleep run 1, 15 minutes; [`cleaning_effect.py`](cleaning_effect.py)):

| Measure | Uncleaned | Cleaned |
|---|---|---|
| Heartbeat artefact, O1, average of 1,229 beats | 86 µV peak-to-peak | 4 µV |
| Sleep-spindle band (sigma, 12–16 Hz) power, scalp mean | 23.5 µV²/Hz | 7.1 µV²/Hz (3.3× lower) |
| Beta band (16–30 Hz) power, scalp mean | 81.6 µV²/Hz | 1.3 µV²/Hz (62× lower) |

![Power spectrum before and after cleaning](../../figures/sub-01_task-sleep_run-1_psd.png)

Classifier comparison across all 33 people: **running**.

### All participants

Updated automatically each time a participant finishes processing. Within-person scores are a preview; the main result is the across-people analysis, added when all 33 are built.

<!-- participants-table:start -->
Participants built: 2 of 33 · updated by `participant_table.py`

**Data quality**

| # | Status | Recordings | Epochs kept (W/N1/N2) | Flagged % | Expert-unscorable | Max bad channels | INPS MNE / refined (dB) | Double-counted beats MNE / refined |
|---|---|---|---|---|---|---|---|---|
| 01 | ok | 5 | 118 (38/46/34) | 9.2 | 0 | 1 | 0.99 / 1.51 | 336 / 0 |
| 02 | ok | 2 | 38 (27/7/4) | 5.0 | 0 | 1 | 1.73 / 1.67 | 122 / 0 |
| 03 | processing | | | | | | | |
| 04 | processing | | | | | | | |
| 05 | processing | | | | | | | |
| 06 | processing | | | | | | | |
| 07 | processing | | | | | | | |
| 08 | processing | | | | | | | |
| 09 | processing | | | | | | | |
| 10 | processing | | | | | | | |
| 11 | processing | | | | | | | |
| 12 | processing | | | | | | | |
| 13 | processing | | | | | | | |
| 14 | processing | | | | | | | |
| 15 | processing | | | | | | | |
| 16 | processing | | | | | | | |
| 17 | processing | | | | | | | |
| 18 | processing | | | | | | | |
| 19 | processing | | | | | | | |
| 20 | processing | | | | | | | |
| 21 | processing | | | | | | | |
| 22 | processing | | | | | | | |
| 23 | processing | | | | | | | |
| 24 | processing | | | | | | | |
| 25 | processing | | | | | | | |
| 26 | processing | | | | | | | |
| 27 | processing | | | | | | | |
| 28 | processing | | | | | | | |
| 29 | processing | | | | | | | |
| 30 | processing | | | | | | | |
| 31 | processing | | | | | | | |
| 32 | processing | | | | | | | |
| 33 | processing | | | | | | | |

**Sleep-staging kappa (logistic regression): Within-person preview (trained on the person's other recordings).** 0 = chance, 1 = perfect; – = not scored (fewer than 3 recordings, or only one stage)

| # | W/N1/N2 raw | W/N1/N2 filt | W/N1/N2 clean-MNE | W/N1/N2 clean-ref | W vs N2 raw | W vs N2 filt | W vs N2 clean-MNE | W vs N2 clean-ref |
|---|---|---|---|---|---|---|---|---|
| 01 | -0.03 | -0.06 | -0.01 | -0.04 | -0.11 | 0.09 | 0.03 | -0.10 |
| 02 | – | – | – | – | – | – | – | – |
| **median** | -0.03 | -0.06 | -0.01 | -0.04 | -0.11 | 0.09 | 0.03 | -0.10 |

**Sleep-staging kappa: Main analysis (trained on all other people):** available when the full build finishes.
<!-- participants-table:end -->

### Preview: participant 1 alone (not the study result)

Scored with [`score_one_person.py`](score_one_person.py): trained on 4 of participant 1's recordings and tested on the fifth, rotating through all five. Same features, models, tasks and quality exclusions as the main analysis. 118 epochs kept (wake 38, N1 46, N2 34; 12 flagged by Autoreject). Full tables: [`results/preview_sub-01_scores.csv`](results/preview_sub-01_scores.csv), [`results/preview_sub-01_quality.csv`](results/preview_sub-01_quality.csv).

**Sleep-staging agreement with the expert** (Cohen's kappa; 0 = chance, 1 = perfect)

| Task | Model | Raw | Filtered | Cleaned (MNE) | Cleaned (refined) |
|---|---|---|---|---|---|
| Wake / N1 / N2 | Logistic regression | −0.03 | −0.06 | −0.01 | −0.04 |
| Wake / N1 / N2 | Gradient boosting | 0.10 | −0.08 | 0.01 | −0.11 |
| Wake vs N2 | Logistic regression | −0.11 | 0.09 | 0.03 | −0.10 |
| Wake vs N2 | Gradient boosting | 0.12 | −0.04 | 0.03 | 0.23 |

**Heartbeat removal** (INPS in dB, higher = more removed; double-counted beats in brackets)

| Recording | MNE detector | Refined detector | Bad channels (PREP) | Epochs flagged |
|---|---|---|---|---|
| Rest 1 | 1.63 (54) | 1.37 (0) | Fp2 | 2 of 20 |
| Rest 2 | 0.10 (8) | 0.05 (0) | — | 3 of 20 |
| Sleep 1 | 0.99 (87) | 1.69 (0) | — | 5 of 30 |
| Sleep 2 | 1.34 (122) | 2.10 (0) | — | 1 of 30 |
| Sleep 3 | 0.88 (65) | 1.51 (0) | F8 | 1 of 30 |

**Reading:** within participant 1, every arm stays near chance, and the order of the arms changes between rows, so this person alone cannot separate them. Likely reasons: about 90 training epochs for 134 features; recordings with very different stage mixes (rest 1 mostly N2, rest 2 mostly wake); and participant 1 being a hard case (in an earlier 5-person code test, wake vs N2 stayed at chance for them in both raw and cleaned data). The refined detector removed more heartbeat artefact in all three sleep recordings and never double-counted. In rest 2 both detectors removed almost nothing and disagree on the heart rate (65 vs 80 bpm): that recording's ECG needs investigating.

## Exploratory diagnostics (not used for scoring)

These scripts use this study's own tests rather than established metrics, so they inform the method but never decide inclusion or results.

- [`data_accounting.py`](data_accounting.py): share of signal each step removes on participant 1: gradient subtraction 99.68% of raw power; the 0.3–40 Hz filter 12.8% of the rest (10.5% below 0.3 Hz, 2.3% above 40 Hz); heartbeat subtraction 19.9% (sigma band 57%); cropping 3.5% of recording time.
- [`overcorrection_check.py`](overcorrection_check.py): the same heartbeat subtraction at heartbeat-like times not locked to the heart removes 3.3–5.1% of band power, close to the method's theoretical 1/21 (4.8%), against 22–57% at real heartbeats.
- [`signal_preservation.py`](signal_preservation.py): the cleaned spectrum keeps the shape of the 24 s recorded before scanning between 0.5 and 15 Hz. That stretch already contains unmarked scanner warm-up (16.7 Hz), so it is an imperfect reference. A 38.5 Hz peak is present before scanning too (scanner-room equipment, not gradient residue), and 3 and 6 Hz peaks appear only during scanning.

![Pre-scan vs cleaned scanning spectrum](results/signal_preservation_sub-01.png)

## Corrections log

- **In-place filtering bug (fixed 22 Oct 2026, before any 33-person results).** MNE's `RawArray` does not copy its input and `filter()` works in place, so building the *filtered* arm altered the data the *cleaned* arm was built from: scanner-artefact removal ran on already-filtered data. Fixed with explicit copies. Participant 1's headline numbers barely moved (sigma 7.2 → 7.1 µV²/Hz; ratios unchanged), but all features are rebuilt.
- **Heartbeat double counting (fixed).** The first detector counted T-waves as beats in some recordings (participant 4: 106 bpm instead of 66).
- **Custom quality rules replaced (22 Oct 2026).** The first version used this study's own tests (random-timing residual, surrogate brain loss, a 2-of-3-window epoch rule). They were replaced by established methods (INPS, standard Autoreject, PREP) and the dataset's own labels, after quality checks on a few recordings of participants 1–4 and before any classification results.
- **Analysis plan revised before results.** After a code test on 4–5 people, logistic regression and the wake-vs-N2 task were added and per-person feature scaling moved to a sensitivity analysis (`--norm`), because people's stage mixes differ hugely (one is 96% wake, another 76% N2).

## Limitations

- Narrow residual artefact peaks remain after cleaning (20–48 Hz; see the spectrum above).
- The artefact templates include the current volume or heartbeat, which subtracts about 1/21 (5%) of that segment's own brain signal.
- Cleaning removes any brain response genuinely locked to the heartbeat (heartbeat-evoked potentials, a few µV); irrelevant for sleep staging, relevant for body–brain research.
- Naps in a scanner contain almost no deep sleep, and only 16 of 33 people have 10 or more minutes of N2.
- 33 people is a small sample; results are reported per person with confidence intervals, not only as one pooled number.

## Reproduce

```bash
python studies/01-preprocessing-ablation/build_dataset.py     # download, clean (4 arms), quality-check, extract features (~10 h)
python src/postprocessing/quality_report.py studies/01-preprocessing-ablation/results   # quality tables + figure
python studies/01-preprocessing-ablation/compare_arms.py      # leave-one-person-out comparison -> results/
python studies/01-preprocessing-ablation/compare_qrs_detectors.py <recording.vhdr> [...]
```
