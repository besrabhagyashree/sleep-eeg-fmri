# Pre-registration: Study 01, Does preprocessing matter?

**Author:** Bhagyashree Besra, Independent Researcher, Odisha, India · ORCID [0009-0008-6118-7602](https://orcid.org/0009-0008-6118-7602)
**Written:** 22 October 2026, before the full 33-participant classification results exist
**Format:** follows the OSF template *Preregistration for secondary data analysis* (existing, publicly available data)
**Repository:** https://github.com/besrabhagyashree/sleep-eeg-fmri (study folder `studies/01-preprocessing-ablation`)

## 1. Research questions and hypotheses

**Q1.** Does removing MRI scanner and heartbeat artefacts from EEG recorded during fMRI improve automatic sleep staging, compared with using the EEG as recorded?
**Q2.** Does simple filtering alone account for any improvement?
**Q3.** Does the choice of heartbeat detector (MNE-Python's standard detector vs the same with timing refinement) change sleep-staging performance?

**H1.** Per-person agreement with the expert (Cohen's kappa) is higher for the *cleaned (MNE)* arm than for the *raw* arm.
**H2.** Kappa for the *filtered* arm is not higher than for the *raw* arm, because filtering cannot remove scanner artefact inside the 0.3–40 Hz band.
**H3.** No directional hypothesis: the two cleaned arms are compared two-sided.

## 2. Data

- **Dataset:** OpenNeuro ds003768, *Simultaneous EEG and fMRI signals during sleep from humans* (Gu et al., 2022, *NeuroImage* 264:119720; doi:10.18112/openneuro.ds003768.v1.0.0). CC0 licence. 33 healthy adults; 32-channel EEG (incl. ECG, EOG) at 5 kHz during resting and sleep fMRI runs; expert sleep-stage labels per 30-s epoch.
- **Variables used:** EEG, ECG and EOG channels; scanner volume triggers (R128); expert stage labels and their uncertain/unscorable flags. fMRI, anatomical and eye-tracking data are not used.
- **Ethics:** secondary analysis of public, de-identified data; no new data collection.

## 3. Prior knowledge of the data (disclosure)

Before writing this plan the author had seen:

- Dataset metadata, file listings, and the distribution of expert stage labels across all 33 participants (W 3,343, N1 2,148, N2 1,325, N3 42 epochs).
- Raw and cleaned EEG, spectra and quality checks for a few recordings of participants 1–4.
- A code test of the classifier on 4–5 participants with an earlier version of the pipeline (results near chance; used only to find bugs and design problems).
- A within-person preview for participant 1 (published in the study README) and data-quality summaries for participants 1–3.

No across-person classification result for the full sample has been computed. Changes made after the above are listed with dates in the study README's corrections log.

## 4. Preprocessing (four arms; everything else identical)

| Arm | EEG |
|---|---|
| raw | As recorded, 5 kHz, no filtering or artefact removal |
| filtered | 0.3–40 Hz FIR filter, resampled to 250 Hz |
| cleaned (MNE) | Gradient artefact: average artefact subtraction locked to R128 triggers, 21-volume template (Allen et al., 2000). Then 0.3–40 Hz, 250 Hz. Heartbeat artefact: average artefact subtraction, 21-beat template (Allen et al., 1998), beats from MNE-Python `find_ecg_events`, unmodified |
| cleaned (refined) | As cleaned (MNE), with each beat placed at the 8–25 Hz ECG energy peak, at most one beat per 0.6 × the MNE beat interval |

Heartbeat removal is skipped for a recording whose heart rate is outside 40–120 bpm (logged).

## 5. Exclusions (judged on the cleaned (MNE) recording; applied identically to all arms)

1. Epochs the expert marked uncertain or unscorable.
2. Epochs not fully inside the scanning period.
3. Epochs whose peak-to-peak amplitude on any good scalp channel exceeds the Autoreject global threshold (Jas et al., 2017) learned per recording.
4. Recordings with more than 3 of 30 scalp channels marked bad by PREP (Bigdely-Shamlo et al., 2015).
5. Participants with more than 25% of epochs flagged by rule 3.

N3 epochs are merged into N2. All exclusions are reported with reasons.

## 6. Features

Per 30-s epoch, for frontal, central, posterior and temporal channel groups: log and relative Welch band power (delta 0.5–4, theta 4–8, alpha 8–12, sigma 12–16, beta 16–30 Hz), total log power, 95% spectral edge frequency, log theta/alpha ratio, median Hjorth mobility and complexity; EOG power at 0.3–2 and 2–8 Hz (67 features), plus their ±2-epoch centred moving average. The ECG channel is never a feature. No per-person feature scaling in the main analysis.

## 7. Models and validation

- **Tasks:** (a) 3-class wake / N1 / N2; (b) wake vs N2.
- **Models:** (i) logistic regression on standardised features, balanced class weights, max 3,000 iterations; (ii) histogram gradient-boosted trees (300 iterations, learning rate 0.05, balanced class weights). Random seed 0.
- **Validation:** leave-one-participant-out. A participant is scored only by a model trained on all other included participants.
- **Baseline:** stratified-random classifier.

## 8. Outcomes and statistical tests

- **Primary outcome:** per-participant Cohen's kappa against the expert, task (a), logistic regression.
- **Primary test (H1):** cleaned (MNE) vs raw, two-sided Wilcoxon signed-rank test across participants with both classes present, α = 0.05; effect reported as the mean difference with a 10,000-sample bootstrap 95% confidence interval.
- **Secondary tests**, reported without correction and labelled exploratory: filtered vs raw (H2), cleaned (refined) vs cleaned (MNE) (H3), cleaned (refined) vs raw, filtered vs cleaned (MNE); the same comparisons for task (b) and for gradient-boosted trees.
- **Signal preservation (descriptive):** per arm, the number of participants whose posterior relative alpha is higher in wake than in N2.
- **Data quality (descriptive):** INPS (Tong et al., 2001) for each heartbeat detector; residual slice-frequency peaks; PREP and Autoreject counts.
- **Sensitivity analysis:** the primary analysis repeated with per-participant robust feature scaling (`--norm`).

## 9. Inference criteria

H1 is supported if the primary test gives p < 0.05 with a positive mean difference; contradicted if p < 0.05 with a negative difference; otherwise inconclusive. Results are reported whichever way they come out.

## Amendment 1: exploratory "fully cleaned" arm (22 October 2026, before full results)

Added after validating three further preprocessing steps on one recording (participant 1, sleep run 3; [`validate_stages.py`](validate_stages.py), results in `results/stages_validation_sub-01_task-sleep_run-3_mne.csv`). **The primary analysis and all hypotheses above are unchanged.** The new arm is exploratory and reported as such.

**Fifth arm, "fully cleaned":** the *cleaned (MNE)* recording plus, in this order (PREP-pipeline order):

1. FIR notch filters at 33.3 Hz (2nd harmonic of the scanner slice frequency) and 38.5 Hz (scanner-room equipment peak present before scanning started), 1 Hz wide (MNE-Python).
2. Spherical-spline interpolation (Perrin et al., 1989) of the channels PREP marked bad for that recording.
3. Re-reference, chosen by the rule below.

**Reference-selection rule (fixed now):** for every included participant with at least 3 wake and 3 N2 epochs, compute under (a) linked mastoids (TP9, TP10) and (b) average reference of all good scalp channels:
- *alpha contrast* = mean posterior (O1, O2, Pz) 8–12 Hz power in wake ÷ in N2;
- *spindle contrast* = mean central (C3, C4, Cz) 12–16 Hz power in N2 ÷ in wake;
- *score* = log(alpha contrast) + log(spindle contrast).

The reference with the higher **median score across participants** is used for the fully cleaned arm. Both references' scores are reported. Ties (difference < 0.01) go to the average reference, the PREP default.

**Movement bursts:** no within-epoch masking is added. Epoch-level exclusion by Autoreject (section 5) remains the movement step, as the established method.

**Optimal basis sets** (Niazy et al., 2005) for residual heartbeat artefact need the recording before heartbeat removal, which the current build does not store. They will be added in a later amendment, before being run.

**Observation recorded before results:** in the validation recording, central 12–16 Hz power was lower in N2 than in wake under every reference (ratio 0.49–0.64; 5 N2 epochs). Whether this holds across participants will be reported.

## Amendment 2: optimal basis sets tested, not adopted (22 October 2026, before full results)

OBS heartbeat removal (Niazy et al., 2005; 4 principal components, the FMRIB toolbox default) was implemented ([`remove_bcg_obs`](../../src/preprocessing/mr_artifacts.py)) and validated on participant 1, sleep run 1 ([`validate_obs.py`](validate_obs.py)). It removed more heartbeat artefact than average subtraction by INPS (6.79 vs 1.69 dB with the refined detector; 2.63 vs 0.99 dB with MNE's), but also 69.6% of all 0.5–30 Hz power. The exploratory random-timing diagnostic showed why: applied at times not locked to the heart, OBS still removed 75% of delta and 32% of theta power (average subtraction: 4–5%). In sleep EEG, slow waves last about as long as one heartbeat and are absorbed into the OBS basis. Because this fails signal preservation in the frequency bands that define sleep stages, **OBS is not added as an arm**. The result is reported as a methods finding, with the caveat that it is this study's implementation of the published method.

## Amendment 3: clarifications to amendment 1 (22 October 2026, before full results)

Following an automated code review:

- The reference-selection score uses only epochs **not** flagged by Autoreject, leaves out recordings with more than 3 bad channels, and leaves out people excluded under the 25% rule.
- **Only the chosen reference** is evaluated as the exploratory arm; the other is reported by its selection score only. Neither is evaluated before the rule has been applied, so the choice cannot be influenced by classification results.
- **Disclosed limitation:** the reference is chosen once using the expert labels of all included participants, including each person later held out in leave-one-person-out testing (non-nested selection). It is a single binary choice made without the classifier and only for the exploratory arm, so the optimistic bias is expected to be small, but it is not zero.
