# Pre-registration: Study 01b, improving classification of N1

**Author:** Bhagyashree Besra (ORCID 0009-0008-6118-7602)
**Registered:** 23 October 2026, before any analysis in this document was run.
**Status of related work:** Study 01 is complete. Its per-stage results, which motivate this study, were seen before writing this plan: for the AAS-MNE arm with gradient boosting, N1 F1 was 0.51; 30% of true N1 epochs were classified as wake and 14% as N2, and 26% of wake epochs as N1.

## 1. Question and hypotheses

N1 is the least reliably scored stage, even between expert scorers (Rosenberg & Van Hout, 2013). Study 01's features summarise each 30-s epoch as a whole, whereas AASM scoring of N1 depends on how much of the epoch contains alpha rhythm, on slow eye movements, and on the surrounding epochs. This study tests whether features and decoding that follow those scoring principles improve N1 classification.

- **H-A (alpha occupancy).** Adding features describing the fraction of each epoch with alpha rhythm present increases per-participant N1 F1 relative to the study 01 classifier.
- **H-B (eye movements).** Adding eye-movement features from the EOG increases per-participant N1 F1 relative to the study 01 classifier.
- **H-C (sequence decoding).** Decoding the study 01 classifier's output with a hidden Markov model of stage transitions increases per-participant N1 F1 relative to epoch-by-epoch prediction.
- **D (benchmark, no hypothesis).** A published, pre-trained sleep stager (YASA; Vallat & Walker, 2021), applied without training on this dataset, is reported for comparison.

## 2. Data

The 29 participants analysed in study 01; the AAS-MNE arm (scanner and heartbeat artefacts removed by average artefact subtraction, 0.3–40 Hz, 250 Hz); the same epochs, exclusions and labels as study 01 (epochs kept after Autoreject; recording 07 sleep run 1 excluded; N3 merged into N2). Three classes: W, N1, N2. Preprocessing is not varied: that question was answered in study 01.

## 3. Methods

**Baseline.** The study 01 spectral features (67 per epoch plus their ±2-epoch averages, 134 inputs) with gradient boosting (primary) and logistic regression (secondary), class-balanced, leave-one-participant-out, exactly as in study 01.

**A. Alpha occupancy** (AASM: N1 is scored when alpha rhythm is attenuated for more than half of the epoch). On the AASM occipital derivation O2–M1 (O1–M2 if an electrode is PREP-bad), each epoch is divided into 15 non-overlapping 2-s windows. In each window, the periodogram (Hann window) gives mean power density in theta (4 ≤ f < 8 Hz) and alpha (8 ≤ f < 12 Hz). A window counts as alpha-present when alpha density exceeds theta density, i.e. when there is an alpha peak above the 1/f background. Features: the fraction of alpha-present windows, and the median over windows of log10(alpha density / theta density); plus their ±2-epoch averages. Added to the baseline inputs.

**B. Eye movements** (AASM: slow eye movements are characteristic of N1). From the EOG channel as recorded, band-pass filtered on the continuous recording into a slow component (0.3–1 Hz) and a fast component (1–5 Hz). Per epoch: log10 power of each component, log10 of their ratio, and the 90th percentile over 2-s windows of the slow component's peak-to-peak amplitude; plus their ±2-epoch averages. Added to the baseline inputs. These are band-limited measures, not a validated slow-eye-movement detector, and the 0.3 Hz high-pass applied in study 01 attenuates the slowest eye movements.

**C. Sequence decoding** (hidden Markov model; Rabiner, 1989). In each cross-validation fold: the 3 × 3 stage-transition matrix and initial-stage probabilities are estimated from the training participants' expert hypnograms (consecutive kept epochs within recordings, add-one smoothing); emission scores are the baseline classifier's predicted probabilities divided by the training class proportions; the most probable stage sequence for each held-out recording is found with the Viterbi algorithm. Applied to the baseline gradient-boosting classifier.

**D. Pre-trained benchmark.** YASA `SleepStaging` (version 0.8.0, default model) on each AAS-MNE recording, with EEG = C4–M1 (C3–M2 if an electrode is PREP-bad), EOG = the EOG channel, no EMG and no metadata. Its probabilities for REM are dropped, N3 is merged into N2, and the remaining probabilities are renormalised; the predicted stage is the most probable of W, N1 and N2.

## 4. Outcomes and tests

- **Primary outcome:** per-participant F1 score for N1, in participants with at least 5 N1 and at least 5 non-N1 epochs.
- **Primary tests:** A vs baseline, B vs baseline and C vs baseline, gradient boosting; two-sided Wilcoxon signed-rank tests on per-participant N1 F1; Holm correction across the three tests; α = 0.05. A hypothesis is supported if its Holm-adjusted p < 0.05 with a positive mean difference, contradicted if p < 0.05 with a negative difference, and otherwise inconclusive. Mean differences are reported with 10,000-sample bootstrap 95% confidence intervals.
- **Secondary (exploratory, uncorrected):** D vs baseline on N1 F1; for every method, per-participant Cohen's κ (three classes), macro F1 and the F1 of W and N2, to check that any N1 gain is not bought at the cost of other stages; the logistic-regression versions of A, B and C; the combination A + B + C.

Results are reported whatever they show.
