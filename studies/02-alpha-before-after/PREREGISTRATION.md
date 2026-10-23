# Pre-registration: Study 02, alpha rhythm before and after a visual-motor task

**Author:** Bhagyashree Besra (ORCID 0009-0008-6118-7602)
**Registered:** 23 October 2026, before any rest-run alpha measure in this document was computed.
**Prior exposure, disclosed:** the rest runs were used in study 01 (sleep staging) and study 01b, and two summary values involving wake alpha were seen there: the mean per-epoch alpha peak across all wake epochs (8.8 Hz) and a per-participant alpha frequency from strong-alpha wake epochs (median 9.5 Hz), both pooled over all recordings, not split by rest run 1 vs 2. No comparison between the two rest runs has been made.

## 1. Question and hypothesis

Each session of OpenNeuro ds003768 contains two 10-minute resting-state runs, the first before and the second after a visual-motor adaptation task (dataset README; task from Albouy et al., 2012). Does the individual alpha frequency (IAF) differ between the two rest runs?

- **H1.** Peak alpha frequency during wake differs between rest run 1 (before the task) and rest run 2 (after). Two-sided; no direction is predicted.

**What the design cannot show.** There is no control condition without the task, so a difference could reflect the task, time spent in the scanner, fatigue or changes in vigilance. Only wake epochs are used, which limits but does not remove the vigilance confound. Whether eyes were open or closed is not documented in the dataset.

## 2. Data

- Participants: the 29 analysed in study 01 (quality rules of study 01 applied).
- Recordings: rest runs 1 and 2, artefact-corrected (AAS-MNE arm of study 01; 0.3–40 Hz, 250 Hz).
- Epochs: expert-scored **wake** epochs not rejected by Autoreject.
- Inclusion: at least 6 such epochs (3 minutes) in **both** rest runs.
- Channels: posterior scalp electrodes O1, O2, Oz, P3, P4, Pz, P7, P8 (recorded reference), averaged.

## 3. Measures

- **Primary: peak alpha frequency (PAF)** by the Savitzky–Golay method of Corcoran et al. (2018), `philistine.mne.savgol_iaf` with default parameters (frequency resolution 0.25 Hz, window length 11, polynomial order 5, alpha band bounds estimated from the data). The included wake epochs of each run are concatenated in time order before estimation. A run without a qualifying alpha peak is recorded as missing.
- **Secondary:**
  - alpha centre of gravity (CoG), same method;
  - FOOOF (Donoghue et al., 2020; `fooof` 1.1.1, default settings, fit 2–40 Hz) on the mean Welch spectrum (4-s windows) of the same epochs: centre frequency, aperiodic-adjusted power of the largest peak in 7–14 Hz, and the aperiodic exponent;
  - log10 absolute alpha power (8–12 Hz) from the same Welch spectrum;
  - the share of each rest run scored as wake.
- **Sensitivity:** the primary analysis repeated with the same number of epochs per run for each participant (the smaller of the two counts, using the earliest epochs of each run).

## 4. Tests

Primary: run 2 − run 1 difference in PAF, two-sided Wilcoxon signed-rank test across participants with a PAF in both runs, α = 0.05; mean difference with a 10,000-sample bootstrap 95% confidence interval. H1 is supported if p < 0.05 and otherwise inconclusive. Secondary measures and the sensitivity analysis are reported with the same test, uncorrected and labelled exploratory. Results are reported whatever they show.
