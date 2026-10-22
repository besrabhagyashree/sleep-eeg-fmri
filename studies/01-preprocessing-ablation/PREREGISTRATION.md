# Pre-registration: Study 01, Does preprocessing matter?

**Author:** Bhagyashree Besra, Independent Researcher, Odisha, India
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
