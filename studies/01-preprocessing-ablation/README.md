<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img alt="Study 01: the same 4 seconds of EEG in four preprocessing arms: raw, filtered only, cleaned with the MNE detector, cleaned with the refined detector" src="assets/banner-light.svg" width="100%">
</picture>

<p align="center">
  <img alt="Status: running" src="https://img.shields.io/badge/status-running-d97706?style=for-the-badge">
  <img alt="4 arms" src="https://img.shields.io/badge/arms-4-33318a?style=for-the-badge">
  <img alt="2 tasks" src="https://img.shields.io/badge/tasks-W%2FN1%2FN2%20%C2%B7%20W%20vs%20N2-b53b6d?style=for-the-badge">
  <img alt="Leave one person out" src="https://img.shields.io/badge/testing-leave--one--person--out-059669?style=for-the-badge">
  <img alt="Established methods only" src="https://img.shields.io/badge/scoring-established%20methods%20only-0b7285?style=for-the-badge">
</p>

<p align="center">
  <a href="#-the-question">Question</a> ·
  <a href="#-design">Design</a> ·
  <a href="#-results">Results</a> ·
  <a href="#-all-participants">All participants</a> ·
  <a href="#-methods">Methods</a> ·
  <a href="#-quality-checks">Quality</a> ·
  <a href="#-corrections-log">Corrections</a> ·
  <a href="#%EF%B8%8F-reproduce">Reproduce</a>
</p>

## ❓ The question

EEG recorded during fMRI is buried under scanner and heartbeat artefacts hundreds of times larger than brain activity (top strip in the banner). Labs routinely remove them before analysis. **But how much does that cleaning change what a sleep-staging model can learn, and how much does the choice of heartbeat detector matter?**

This study answers with an **ablation**: the same classifier, trained and tested on the same people and expert labels, using four versions of the same EEG.

| | Arm | EEG used |
|:---:|---|---|
| ⬜ | **raw** | Straight from the dataset: 5 kHz, nothing removed or filtered |
| 🟧 | **filtered** | 0.3–40 Hz filter, 250 Hz, no artefact removal |
| 🟪 | **cleaned (MNE)** | Scanner and heartbeat artefacts removed, then the same filter; heartbeats found by MNE-Python's standard detector, unmodified |
| 🟩 | **cleaned (refined)** | The same, with each detected beat aligned to its ECG peak (one beat per interval) |

## 🧭 Design

```mermaid
flowchart LR
    EEG["🧠 Same EEG<br/>33 people · 6,858 epochs"]:::data
    EEG --> A1["⬜ raw"]:::raw
    EEG --> A2["🟧 filtered"]:::filt
    EEG --> A3["🟪 cleaned · MNE"]:::mne
    EEG --> A4["🟩 cleaned · refined"]:::ref
    A1 & A2 & A3 & A4 --> F["Same 67 features<br/>+ context"]:::same
    F --> M["Same models<br/>logistic regression · boosted trees"]:::same
    M --> T["Leave-one-person-out<br/>Cohen's kappa per person"]:::same
    T --> S["Paired Wilcoxon tests<br/>+ 95% CIs between arms"]:::stat
    LAB["📋 Expert labels<br/>W · N1 · N2"]:::data --> T

    classDef data fill:#ede9fe,stroke:#6d28d9,color:#2e1065
    classDef raw fill:#f1f5f9,stroke:#64748b,color:#0f172a
    classDef filt fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef mne fill:#e0e7ff,stroke:#4338ca,color:#1e1b4b
    classDef ref fill:#d1fae5,stroke:#059669,color:#064e3b
    classDef same fill:#f8fafc,stroke:#94a3b8,color:#0f172a
    classDef stat fill:#fce7f3,stroke:#be185d,color:#500724
```

Only the EEG differs between arms. Epochs, people, quality exclusions, features, models and tests are identical.

## 📊 Results

> [!IMPORTANT]
> **Summary.** Artefact correction did not significantly improve the pre-registered primary outcome (Δκ = 0.056, 95% CI [−0.020, 0.137], p = 0.33; H1 inconclusive). Exploratory analyses indicate that its benefit is model-dependent (consistent for gradient boosting, absent for logistic regression), larger in participants who slept for most of the recording, and that correction attenuates a residual cardiac confound present in uncorrected data. Adding sleep-event features (spindles, slow waves, alpha peak) did not change these conclusions. All reported statistics were independently recomputed from the saved data by a separate audit script; features, kappas, test statistics, exclusions and epoch counts matched.

Notation: κ, Cohen's kappa against the expert hypnogram; Δκ, mean paired difference in per-participant κ (second arm minus first); CI, 10,000-sample bootstrap 95% confidence interval of Δκ; W, Wilcoxon signed-rank statistic; n, participants with a non-zero difference. Arms: **raw** (5 kHz, uncorrected), **filtered** (0.3–40 Hz, 250 Hz), **AAS-MNE** and **AAS-refined** (gradient and ballistocardiogram average artefact subtraction with MNE's or the refined R-peak detector), **full** (AAS-MNE plus notch, interpolation and linked-mastoid re-reference; exploratory).

### Sample

Of 33 participants, **29 were analysed** (5,009 epochs per arm: wake 2,541, N1 1,579, N2 889; N3 merged into N2). Four participants were excluded under rule 5 (more than 25% of epochs rejected by Autoreject: 03, 13, 17, 31) and one recording under rule 4 (more than three PREP bad channels: 07, sleep run 1). Classification used leave-one-participant-out cross-validation. The reference for the full arm was fixed by the amendment-1 rule before any comparison was run: linked mastoids (median selection score 0.54 vs 0.26 for the average reference; n = 23 participants with at least three wake and three N2 epochs).

### Pre-registered hypotheses

Primary outcome: per-participant κ, three-class staging (W/N1/N2), logistic regression; two-sided Wilcoxon signed-rank tests, α = 0.05.

| | Contrast | Δκ [95% CI] | W (n) | p | Better / worse | Conclusion |
|---|---|:---:|:---:|:---:|:---:|---|
| **H1** | AAS-MNE − raw | 0.056 [−0.020, 0.137] | 160 (28) | 0.33 | 15 / 13 | Inconclusive |
| H2 | filtered − raw | 0.015 [−0.005, 0.035] | 121 (26) | 0.17 | 15 / 11 | Consistent with H2 |
| H3 | AAS-refined − AAS-MNE | 0.016 [−0.005, 0.042] | 168 (27) | 0.61 | 11 / 16 | No detector effect |

Pooled κ over all epochs (chance-level baseline: −0.006 three-class, −0.040 W vs N2):

| Task, classifier | Raw | Filtered | AAS-MNE | AAS-refined | Full |
|---|:---:|:---:|:---:|:---:|:---:|
| W/N1/N2, logistic regression | 0.27 | 0.29 | 0.28 | 0.29 | 0.34 |
| W/N1/N2, gradient boosting | 0.31 | 0.28 | 0.37 | 0.36 | 0.36 |
| W vs N2, logistic regression | 0.41 | 0.46 | 0.44 | 0.45 | 0.47 |
| W vs N2, gradient boosting | 0.41 | 0.31 | 0.56 | 0.55 | 0.53 |

### Secondary comparisons (exploratory, uncorrected)

Of approximately 30 pre-specified secondary contrasts, reported without correction for multiplicity, five reached p < 0.05; one or two are expected by chance.

| Task, classifier | Contrast | Δκ | p | Better / worse |
|---|---|:---:|:---:|:---:|
| W vs N2, gradient boosting | AAS-MNE − filtered | 0.149 | 0.003 | 17 / 5 |
| W/N1/N2, gradient boosting | AAS-MNE − filtered | 0.066 | 0.023 | 21 / 7 |
| W vs N2, gradient boosting | AAS-MNE − raw | 0.100 | 0.050\* | 13 / 8 |
| W vs N2, logistic regression | filtered − raw | 0.125 | 0.048 | 12 / 8 |
| W vs N2, logistic regression | AAS-MNE − filtered | −0.107 | 0.017 | 6 / 16 |

\*Zero differences discarded (four participants); with Pratt or zero-split handling, p ≈ 0.07.

Effects of correction diverged between classifiers: gradient boosting benefited consistently from artefact correction, whereas logistic regression did not, and in one contrast favoured the filtered arm. None of these contrasts survives Bonferroni correction across the ~30 secondary tests (smallest adjusted p ≈ 0.08).

**Signal preservation.** Posterior relative alpha power was higher in wake than in N2 in 23 of 25 participants with both stages after AAS-MNE correction (22 of 25 for AAS-refined and full), compared with 20 of 25 (raw) and 19 of 25 (filtered).

**Sensitivity analysis.** With per-participant robust feature scaling, all contrasts attenuated (primary Δκ = 0.013, p = 0.72; W vs N2, gradient boosting, AAS-MNE − raw: Δκ = 0.070, p = 0.18), consistent with the pre-registered concern that within-participant scaling removes between-participant differences in stage composition.

### Residual cardiac confound (amendment 5, exploratory)

Within each expert stage, the Spearman correlation between epoch heart rate and the classifier's N2 prediction was computed per participant and tested against zero across participants. A negative correlation indicates that, for epochs of the same true stage, lower heart rate increases the probability of an N2 prediction. Heart rate was lower in N2 than in wake by a median of 3.3 bpm (16 of 25 participants).

| Arm | Gradient boosting: median ρ (negative / n) | p | Logistic regression: median ρ | p |
|---|:---:|:---:|:---:|:---:|
| Raw | −0.17 (17 / 21) | 0.0007 | −0.08 | 0.064 |
| Filtered | −0.14 (15 / 20) | 0.024 | −0.09 | 0.13 |
| AAS-MNE | −0.10 (16 / 23) | 0.056 | 0.05 | 0.96 |
| AAS-refined | −0.14 (14 / 22) | 0.11 | 0.02 | 0.89 |
| Full | −0.06 (13 / 23) | 0.54 | −0.17 | 0.12 |

In uncorrected data, gradient-boosting predictions covaried with heart rate within expert stages (p = 0.0007; Bonferroni-adjusted across the ten tests, p = 0.007), consistent with ballistocardiogram activity contributing to classification. The association was weaker and non-significant after correction. Classification performance on uncorrected data may therefore partly reflect a cardiac rather than a neural signal; because heart rate itself differs between stages, this analysis cannot fully separate the two.

### Post-hoc subset: participants who slept (amendment 8)

This analysis was specified after partial primary results had been inspected and is reported as hypothesis-generating. It was restricted to the 14 participants who met all quality criteria and were awake for less than 50% of usable epochs (01, 04, 07, 09, 11, 14, 15, 16, 18, 19, 23, 24, 25, 27), with leave-one-participant-out validation within the subset and the reference selected on the full sample.

| Task, classifier | Contrast | Δκ [95% CI] | p | Better / worse |
|---|---|:---:|:---:|:---:|
| W/N1/N2, logistic regression | AAS-MNE − raw | 0.102 [0.016, 0.194] | 0.049 | 10 / 4 |
| W vs N2, logistic regression | AAS-MNE − raw | 0.179 [0.061, 0.310] | 0.009 | 12 / 2 |
| W vs N2, gradient boosting | AAS-MNE − raw | 0.163 [0.021, 0.314] | 0.016 | 12 / 1 |

In this subset, pooled three-class κ increased from 0.09 (raw) to 0.27 (AAS-MNE), suggesting that the benefit of correction is concentrated in participants with substantial sleep. One possible explanation, not tested here, is that in wake-dominant participants uncorrected features already suffice to identify the predominant class, diluting the average effect in the full sample. Given its post-hoc definition, the absence of correction for multiplicity and n = 14, this result motivates a prospective test rather than qualifying the primary conclusion.

### Sleep-stage transition structure (descriptive)

![Stage transitions: group diagram, per-person grids and pattern check](results/transitions_sleepers.png)

First-order transitions between consecutive 30-s epochs of the expert hypnograms were tabulated for the 14 participants of the post-hoc subset (uncertain or unscorable epochs interrupt sequences).

| Property | Pooled estimate | Participants conforming |
|---|---|:---:|
| Sleep onset via N1 | 217 of 220 transitions out of wake entered N1 | 14 / 14 |
| Transitions between adjacent stages | 95% of all stage changes | 13 / 14 |
| Stage persistence increases with depth | P(stay): W 0.72, N1 0.75, N2 0.81, N3 0.90 | 10 / 14 (N2 > N1) |
| N1 as a bidirectional transitional state | P(N1→W) = P(N1→N2) = 0.123 | 13 / 14 |
| Awakening from N2 via N1 | N2→N1: 112; N2→W: 28 | 12 / 14 |

These properties correspond to the canonical organisation of human sleep: entry into sleep through stage N1, a transitional and readily reversible state (Carskadon & Dement, 2005; Ogilvie, 2001), and stage-transition probabilities and bout durations of the type used to characterise normal and disordered sleep (Kishi et al., 2008; Bianchi et al., 2010), with distinct statistics for wake and sleep bouts (Lo et al., 2004). Their presence supports the internal validity of the expert scoring. The data departed from typical nocturnal sleep in their fragmentation (median bout duration 0.5–1 min) and scarcity of N3, as reported for sleep during fMRI acquisition (Tagliazucchi & Laufs, 2014). Part of this regularity is attributable to the scoring rules, which favour stage continuity.

### Sleep-event feature set (amendments 6 and 7, secondary)

The comparison was repeated with the 67 spectral features augmented by sleep-event features: YASA spindle and slow-wave detection and the posterior alpha peak, computed on AASM derivations (C4–M1, F4–M1, O2–M1; backups only for PREP-bad electrodes, used for 3% of epochs). Sample, epochs, exclusions, classifiers and tests were identical to the primary analysis (29 participants, 5,009 epochs per arm).

| Task, classifier | Contrast | Δκ [95% CI] | W (n) | p | Better / worse |
|---|---|:---:|:---:|:---:|:---:|
| W/N1/N2, logistic regression | AAS-MNE − raw | 0.058 [−0.004, 0.124] | 142 (28) | 0.16 | 16 / 12 |
| W/N1/N2, logistic regression | AAS-refined − raw | 0.092 [0.027, 0.165] | 105 (28) | 0.026 | 19 / 9 |
| W/N1/N2, logistic regression | filtered − raw | 0.012 [−0.016, 0.040] | 128 (25) | 0.35 | 16 / 9 |
| W vs N2, gradient boosting | AAS-MNE − raw | 0.079 [−0.024, 0.181] | 86 (23) | 0.11 | 15 / 8 |
| W vs N2, gradient boosting | AAS-MNE − filtered | 0.138 [0.035, 0.245] | 68 (23) | 0.033 | 17 / 6 |

The pattern replicated the spectral analysis: the contrast corresponding to H1 was again positive but not significant (Δκ = 0.058, p = 0.16), filtering alone conferred no benefit, and correction improved gradient-boosting W vs N2 classification relative to filtered data. Pooled κ was within ±0.03 of the spectral-only values in every arm (e.g. W vs N2, gradient boosting, AAS-MNE: 0.58 vs 0.56). All contrasts are exploratory and uncorrected.

Adding event features did not measurably change per-participant agreement (exploratory paired comparison with the spectral-only analysis, same arm: Δκ between −0.009 and 0.031, all p > 0.37). A likely reason is that the spectral set already captures the energy of these events (sigma and delta band power), and that spindles were rare in this in-scanner dataset. Event features therefore added no detectable information for staging here, and the conclusions of the primary analysis do not depend on the feature set.

#### Validity of slow-wave detection across arms (exploratory)

Although event features did not improve classification, the arms differed markedly in whether a published detector could recover physiologically plausible events. Slow waves increase from wake through N1 to N2, and are not expected in wake. For each participant with both stages (n = 25), the mean slow-wave rate (YASA, F4–M1) was compared between N2 and wake epochs (two-sided Wilcoxon signed-rank).

| Arm | Median rate, events/min (W · N1 · N2) | N2 > W | W statistic, p | Wake epochs with ≥ 1 detection |
|---|:---:|:---:|:---:|:---:|
| Raw | 0.0 · 0.0 · 0.0 | 4 / 25 | 0, p = 0.068 | 1% |
| Filtered | 5.7 · 7.0 · 11.5 | 20 / 25 | 44, p = 0.0008 | 74% |
| AAS-MNE | 2.1 · 4.0 · 4.8 | 19 / 25 | 46, p = 0.001 | 52% |
| AAS-refined | 2.0 · 3.8 · 4.7 | 20 / 25 | 28, p < 0.001 | 47% |

Artefact correction had two effects on event detection. Relative to uncorrected data, it made detection possible: on raw recordings the detector returned almost no events, because gradient-artefact amplitude exceeded its plausibility limits. Relative to filtering alone, it improved specificity: the expected N2 > wake gradient was present in both filtered and corrected data, but filtered data yielded detections in 74% of wake epochs, and a median wake rate about three times that after correction (5.7 vs 2.1 events/min), consistent with residual scanner and ballistocardiogram activity being counted as slow waves. Detection was not fully specific after correction: 47–52% of wake epochs still contained at least one event, plausibly reflecting eye movements or residual cardiac activity at the frontal derivation. Thus, beyond its effect on staging accuracy, correction is a precondition for valid application of standard sleep-event detectors to in-scanner EEG.

Spindle detection did not show a physiological pattern in any arm: no events were detected in raw or filtered data, and after correction spindle rates were higher in wake than in N2 (mean 0.97 vs 0.57 events/min; N2 > W in 8 of 25 participants). Because detection was run on the full recording without the hypnogram (to prevent label leakage), events in wake are likely false positives, possibly high-frequency alpha activity; this interpretation was not verified by inspecting the detected events.

<details>
<summary><b>📈 Per-participant κ by arm, and confusion matrices</b></summary>

![Per-participant kappa by arm](results/kappa_by_arm.png)

![Confusion matrices](results/confusion_matrices.png)
</details>

**What cleaning does to the signal** (participant 1, sleep run 1; [`cleaning_effect.py`](cleaning_effect.py)):

| | Uncleaned | Cleaned |
|---|:---:|:---:|
| 💓 Heartbeat artefact (O1, average of 1,229 beats) | 86 µV | **4 µV** |
| 🌙 Sleep-spindle band power (12–16 Hz) | 23.5 µV²/Hz | **7.1 µV²/Hz** · 3.3× lower |
| 📡 Beta band power, mostly scanner noise (16–30 Hz) | 81.6 µV²/Hz | **1.3 µV²/Hz** · 62× lower |

<details>
<summary><b>📈 Power spectrum before and after cleaning</b></summary>

![Power spectrum before and after cleaning](../../figures/sub-01_task-sleep_run-1_psd.png)
</details>

## 👥 All participants

Updated each time a participant finishes processing, by [`participant_table.py`](participant_table.py). Click a heading to open its table.

<!-- participants-table:start -->
<img alt="progress" src="https://img.shields.io/badge/participants%20built-33%20of%2033-059669?style=for-the-badge"> <img alt="percent" src="https://img.shields.io/badge/progress-100%25-33318a?style=for-the-badge">

**Kappa colours** follow the Landis & Koch (1977) agreement bands: ⬛ ≤ 0 none · 🟥 0.01–0.20 slight · 🟧 0.21–0.40 fair · 🟨 0.41–0.60 moderate · 🟩 0.61–0.80 substantial · 💚 0.81–1.00 almost perfect

<details open>
<summary><b>🎯 Main result: scored by a model trained on all other people</b></summary>

Logistic regression · Cohen's kappa vs the expert · – = not scored (fewer than 3 recordings, or only one stage)

| # | W/N1/N2<br>raw | W/N1/N2<br>filt | W/N1/N2<br>clean-MNE | W/N1/N2<br>clean-ref | W vs N2<br>raw | W vs N2<br>filt | W vs N2<br>clean-MNE | W vs N2<br>clean-ref |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 01 | ⬛ 0.00 | 🟥 0.15 | ⬛ -0.07 | ⬛ -0.11 | ⬛ 0.00 | 🟨 0.58 | 🟥 0.02 | 🟥 0.02 |
| 02 | ⬛ 0.00 | ⬛ 0.00 | 🟨 0.52 | 🟨 0.54 | ⬛ 0.00 | ⬛ 0.00 | ⬛ 0.00 | ⬛ 0.00 |
| 03 | – | – | – | – | – | – | – | – |
| 04 | 🟧 0.35 | 🟧 0.39 | 🟧 0.27 | 🟧 0.25 | 💚 0.86 | 🟩 0.80 | 🟩 0.77 | 🟩 0.79 |
| 05 | 🟥 0.02 | 🟥 0.02 | 🟧 0.29 | 🟧 0.28 | 🟧 0.27 | 🟥 0.20 | ⬛ -0.02 | ⬛ -0.02 |
| 06 | 🟧 0.29 | 🟧 0.29 | 🟧 0.39 | 🟨 0.41 | ⬛ 0.00 | 🟩 0.65 | 🟩 0.67 | 🟩 0.78 |
| 07 | 🟥 0.04 | 🟥 0.14 | 🟧 0.38 | 🟧 0.39 | 🟩 0.66 | 🟥 0.06 | ⬛ -0.02 | 🟩 0.66 |
| 08 | ⬛ 0.00 | ⬛ 0.00 | ⬛ 0.00 | ⬛ 0.00 | – | – | – | – |
| 09 | ⬛ -0.06 | ⬛ 0.00 | 🟧 0.39 | 🟧 0.38 | 🟥 0.04 | 🟩 0.76 | 🟩 0.72 | 🟩 0.80 |
| 10 | 🟥 0.10 | 🟥 0.16 | 🟧 0.29 | 🟧 0.23 | 🟨 0.50 | 🟨 0.47 | 🟨 0.57 | 🟨 0.60 |
| 11 | 🟥 0.14 | 🟥 0.18 | 🟥 0.04 | 🟥 0.14 | 🟥 0.06 | 🟧 0.35 | 🟥 0.11 | 🟧 0.34 |
| 12 | ⬛ -0.11 | ⬛ -0.13 | ⬛ -0.01 | ⬛ -0.02 | ⬛ -0.07 | 🟥 0.08 | ⬛ -0.05 | ⬛ -0.01 |
| 13 | – | – | – | – | – | – | – | – |
| 14 | ⬛ -0.01 | ⬛ 0.00 | ⬛ -0.02 | ⬛ -0.03 | 🟥 0.08 | 🟥 0.17 | ⬛ -0.09 | ⬛ -0.08 |
| 15 | 🟨 0.55 | 🟨 0.59 | 🟧 0.27 | 🟨 0.52 | 🟩 0.70 | 💚 0.93 | 🟧 0.35 | 🟩 0.70 |
| 16 | 🟨 0.55 | 🟨 0.46 | 🟧 0.21 | 🟥 0.17 | ⬛ 0.00 | ⬛ -0.03 | ⬛ -0.03 | ⬛ -0.03 |
| 17 | – | – | – | – | – | – | – | – |
| 18 | 🟥 0.12 | 🟧 0.22 | 🟥 0.01 | 🟥 0.01 | 🟨 0.49 | 🟨 0.49 | 🟨 0.49 | 🟨 0.49 |
| 19 | ⬛ -0.06 | ⬛ -0.07 | 🟥 0.09 | 🟥 0.04 | ⬛ -0.19 | ⬛ -0.19 | 🟥 0.15 | 🟥 0.20 |
| 20 | 🟥 0.01 | 🟥 0.09 | 🟥 0.02 | ⬛ 0.00 | – | – | – | – |
| 21 | 🟥 0.11 | 🟥 0.07 | 🟥 0.16 | 🟥 0.19 | – | – | – | – |
| 22 | 🟥 0.06 | 🟥 0.12 | ⬛ 0.00 | 🟥 0.08 | ⬛ 0.00 | 🟩 0.71 | 🟧 0.24 | 🟧 0.25 |
| 23 | 🟧 0.29 | 🟧 0.31 | 🟧 0.28 | 🟧 0.27 | 🟧 0.22 | 🟧 0.35 | 🟨 0.54 | 🟧 0.40 |
| 24 | ⬛ -0.02 | ⬛ -0.02 | 🟥 0.11 | 🟧 0.25 | ⬛ -0.38 | 🟥 0.03 | 🟥 0.03 | 🟥 0.01 |
| 25 | 🟥 0.13 | 🟥 0.02 | ⬛ 0.00 | ⬛ -0.03 | ⬛ -0.14 | 🟥 0.09 | 🟥 0.09 | ⬛ 0.00 |
| 26 | ⬛ 0.00 | ⬛ 0.00 | 🟨 0.54 | 🟨 0.59 | – | – | – | – |
| 27 | 🟧 0.26 | 🟧 0.25 | 🟥 0.05 | 🟥 0.14 | 🟧 0.37 | 🟨 0.48 | 🟥 0.08 | 🟥 0.14 |
| 28 | 🟩 0.66 | 🟩 0.62 | 🟨 0.50 | 🟨 0.48 | 🟩 0.76 | 🟩 0.74 | 🟨 0.60 | 🟨 0.60 |
| 29 | 🟧 0.31 | 🟧 0.24 | 🟩 0.61 | 🟩 0.67 | 💚 0.92 | 💚 0.87 | 💚 0.87 | 💚 0.87 |
| 30 | 🟥 0.10 | 🟥 0.10 | ⬛ 0.00 | ⬛ 0.00 | 🟨 0.49 | 🟥 0.18 | ⬛ 0.00 | ⬛ 0.00 |
| 31 | – | – | – | – | – | – | – | – |
| 32 | ⬛ -0.01 | ⬛ -0.01 | 🟥 0.04 | 🟥 0.04 | ⬛ 0.00 | ⬛ 0.00 | 🟥 0.03 | 🟥 0.02 |
| 33 | 🟥 0.04 | 🟥 0.10 | 🟥 0.12 | 🟥 0.08 | ⬛ 0.00 | ⬛ 0.00 | ⬛ -0.03 | ⬛ -0.05 |
| **median** | **🟥 0.06** | **🟥 0.10** | **🟥 0.12** | **🟥 0.17** | **🟥 0.06** | **🟧 0.35** | **🟥 0.09** | **🟥 0.20** |

</details>

<details>
<summary><b>🔍 Within-person preview: trained on the person's other recordings</b></summary>

Logistic regression · Cohen's kappa vs the expert · – = not scored (fewer than 3 recordings, or only one stage)

| # | W/N1/N2<br>raw | W/N1/N2<br>filt | W/N1/N2<br>clean-MNE | W/N1/N2<br>clean-ref | W vs N2<br>raw | W vs N2<br>filt | W vs N2<br>clean-MNE | W vs N2<br>clean-ref |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 01 | ⬛ -0.03 | ⬛ -0.06 | ⬛ -0.01 | ⬛ -0.04 | ⬛ -0.11 | 🟥 0.09 | 🟥 0.03 | ⬛ -0.10 |
| 02 | – | – | – | – | – | – | – | – |
| 03 | ⬛ -0.03 | ⬛ -0.11 | ⬛ -0.02 | ⬛ -0.02 | ⬛ -0.02 | ⬛ -0.02 | 🟧 0.39 | 🟧 0.39 |
| 04 | 🟧 0.39 | 🟧 0.30 | 🟨 0.41 | 🟨 0.42 | 💚 0.86 | 💚 0.83 | 💚 0.93 | 💚 0.90 |
| 05 | 🟧 0.31 | 🟧 0.32 | ⬛ -0.01 | ⬛ -0.07 | ⬛ -0.03 | ⬛ -0.03 | ⬛ -0.04 | ⬛ -0.03 |
| 06 | ⬛ -0.10 | 🟥 0.10 | 🟥 0.18 | 🟥 0.09 | ⬛ -0.12 | ⬛ -0.11 | ⬛ -0.11 | ⬛ -0.11 |
| 07 | 🟥 0.16 | 🟥 0.09 | 🟥 0.10 | 🟥 0.09 | ⬛ -0.04 | ⬛ -0.03 | ⬛ -0.04 | ⬛ -0.03 |
| 08 | ⬛ -0.01 | ⬛ -0.01 | ⬛ -0.01 | ⬛ -0.01 | – | – | – | – |
| 09 | 🟧 0.37 | 🟧 0.39 | 🟨 0.48 | 🟨 0.49 | 🟩 0.65 | 🟩 0.67 | 💚 0.89 | 💚 0.91 |
| 10 | 🟥 0.17 | 🟧 0.24 | 🟧 0.39 | 🟧 0.40 | 🟧 0.30 | 🟧 0.40 | 🟨 0.44 | 🟨 0.50 |
| 11 | 🟧 0.31 | 🟧 0.28 | 🟥 0.16 | 🟥 0.13 | ⬛ -0.11 | ⬛ -0.11 | 🟧 0.29 | 🟧 0.29 |
| 12 | 🟥 0.14 | 🟧 0.34 | ⬛ -0.54 | ⬛ -0.47 | ⬛ -0.15 | ⬛ -0.16 | ⬛ -0.22 | ⬛ -0.24 |
| 13 | ⬛ -0.04 | ⬛ 0.00 | 🟥 0.11 | 🟥 0.06 | ⬛ -0.16 | ⬛ -0.15 | ⬛ -0.14 | ⬛ -0.12 |
| 14 | 🟥 0.01 | 🟥 0.03 | 🟥 0.18 | 🟥 0.19 | 🟨 0.43 | 🟨 0.51 | 🟩 0.61 | 🟩 0.69 |
| 15 | 🟨 0.45 | 🟨 0.47 | 🟨 0.52 | 🟨 0.56 | 💚 0.96 | 💚 0.96 | 💚 0.98 | 💚 0.98 |
| 16 | ⬛ -0.01 | 🟥 0.10 | ⬛ -0.04 | 🟥 0.17 | 🟥 0.14 | 🟩 0.66 | ⬛ -0.03 | 🟥 0.11 |
| 17 | 🟥 0.16 | 🟥 0.19 | ⬛ -0.07 | 🟥 0.13 | ⬛ -0.08 | ⬛ -0.11 | ⬛ -0.07 | ⬛ -0.08 |
| 18 | 🟧 0.22 | 🟧 0.25 | 🟧 0.34 | 🟧 0.36 | 🟥 0.09 | ⬛ -0.09 | 🟧 0.37 | 🟧 0.37 |
| 19 | 🟥 0.13 | 🟥 0.07 | ⬛ -0.09 | ⬛ -0.01 | 🟥 0.11 | 🟥 0.16 | ⬛ -0.13 | ⬛ -0.10 |
| 20 | 🟥 0.15 | 🟧 0.22 | 🟥 0.06 | 🟥 0.06 | – | – | – | – |
| 21 | – | – | – | – | – | – | – | – |
| 22 | 🟧 0.21 | 🟧 0.40 | 🟥 0.20 | 🟧 0.25 | 💚 0.96 | 💚 0.91 | 💚 0.92 | 💚 0.96 |
| 23 | ⬛ -0.22 | 🟥 0.03 | 🟥 0.04 | 🟥 0.08 | ⬛ -0.06 | 🟧 0.21 | 🟧 0.26 | 🟧 0.24 |
| 24 | 🟥 0.04 | ⬛ -0.03 | 🟥 0.09 | 🟥 0.06 | 🟥 0.19 | 🟥 0.15 | 🟧 0.38 | 🟥 0.03 |
| 25 | 🟥 0.11 | 🟥 0.16 | 🟥 0.05 | ⬛ -0.02 | ⬛ 0.00 | ⬛ 0.00 | ⬛ 0.00 | ⬛ 0.00 |
| 26 | 🟥 0.18 | 🟥 0.18 | 🟧 0.34 | 🟧 0.21 | – | – | – | – |
| 27 | 🟨 0.42 | 🟧 0.33 | 🟨 0.48 | 🟨 0.53 | 🟩 0.77 | 🟩 0.77 | 🟩 0.74 | 🟩 0.70 |
| 28 | 🟨 0.45 | 🟧 0.40 | 🟧 0.29 | 🟧 0.31 | 🟨 0.54 | 🟨 0.54 | 🟨 0.49 | 🟨 0.53 |
| 29 | 🟧 0.37 | 🟧 0.35 | 🟨 0.42 | 🟨 0.52 | ⬛ -0.02 | ⬛ -0.01 | ⬛ 0.00 | ⬛ 0.00 |
| 30 | 🟥 0.14 | 🟥 0.12 | ⬛ -0.03 | 🟥 0.01 | 🟩 0.64 | 🟥 0.20 | 🟨 0.59 | 🟨 0.56 |
| 31 | ⬛ -0.01 | 🟥 0.07 | 🟧 0.34 | 🟥 0.02 | ⬛ -0.10 | 🟧 0.29 | 🟥 0.11 | ⬛ -0.05 |
| 32 | ⬛ -0.14 | ⬛ -0.18 | ⬛ -0.12 | ⬛ -0.08 | ⬛ -0.14 | ⬛ -0.14 | ⬛ -0.12 | 🟥 0.03 |
| 33 | 🟧 0.29 | 🟧 0.34 | 🟧 0.26 | 🟧 0.21 | ⬛ -0.05 | ⬛ -0.04 | ⬛ -0.02 | ⬛ -0.02 |
| **median** | **🟥 0.15** | **🟥 0.18** | **🟥 0.11** | **🟥 0.09** | **⬛ -0.01** | **🟥 0.12** | **🟥 0.18** | **🟥 0.07** |

</details>

<details>
<summary><b>🩺 Data quality per participant</b></summary>

✅/❌ against the pre-set conventions: ≤ 3 bad channels (PREP) per recording; ≤ 25% of epochs flagged (Autoreject). INPS has no published threshold, so it is shown without a colour.

| # | Status | Recordings | Epochs kept<br>(W / N1 / N2) | Flagged | Expert-<br>unscorable | Bad channels<br>(max) | INPS dB<br>MNE / refined | Double-counted beats<br>MNE / refined |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 01 | ✅ ok | 5 | 118 (38 / 46 / 34) | ✅ 9.2% | 0 | ✅ 1 | 0.99 / 1.51 | 336 / 0 |
| 02 | ✅ ok | 2 | 38 (27 / 7 / 4) | ✅ 5.0% | 0 | ✅ 1 | 1.73 / 1.67 | 122 / 0 |
| 03 | ❌ excluded (> 25% epochs flagged) | 10 | 206 (2 / 38 / 166) | ❌ 26.2% | 1 | ✅ 2 | 2.13 / 2.41 | 246 / 0 |
| 04 | ✅ ok | 9 | 221 (89 / 87 / 45) | ✅ 11.6% | 0 | ✅ 1 | 1.61 / 1.49 | 1411 / 0 |
| 05 | ✅ ok | 8 | 195 (172 / 19 / 4) | ✅ 11.4% | 0 | ✅ 1 | 1.52 / 1.59 | 555 / 0 |
| 06 | ✅ ok | 6 | 131 (108 / 13 / 10) | ✅ 18.1% | 0 | ✅ 2 | 2.44 / 2.75 | 16 / 0 |
| 07 | ✅ ok | 7 | 120 (2 / 58 / 60) | ✅ 14.9% | 22 | ❌ 4 | 0.69 / 0.73 | 197 / 0 |
| 08 | ✅ ok | 9 | 210 (208 / 2 / 0) | ✅ 15.0% | 3 | ✅ 1 | 1.33 / 1.52 | 383 / 0 |
| 09 | ✅ ok | 8 | 180 (54 / 72 / 54) | ✅ 17.4% | 2 | ✅ 1 | 3.58 / 3.95 | 144 / 0 |
| 10 | ✅ ok | 8 | 189 (107 / 40 / 42) | ✅ 14.1% | 0 | ✅ 1 | 2.89 / 2.34 | 65 / 0 |
| 11 | ✅ ok | 8 | 146 (48 / 95 / 3) | ✅ 24.4% | 27 | ✅ 1 | 0.67 / 1.09 | 790 / 0 |
| 12 | ✅ ok | 5 | 99 (61 / 29 / 9) | ✅ 23.8% | 0 | ✅ 1 | 3.24 / 3.50 | 64 / 0 |
| 13 | ❌ excluded (> 25% epochs flagged) | 6 | 108 (86 / 9 / 13) | ❌ 32.5% | 0 | ✅ 2 | 0.82 / 0.96 | 272 / 0 |
| 14 | ✅ ok | 9 | 218 (28 / 173 / 17) | ✅ 12.8% | 0 | ✅ 1 | 0.73 / 0.66 | 909 / 27 |
| 15 | ✅ ok | 8 | 196 (58 / 85 / 53) | ✅ 10.9% | 0 | ✅ 1 | 1.94 / 2.35 | 437 / 0 |
| 16 | ✅ ok | 10 | 168 (2 / 51 / 115) | ✅ 16.4% | 0 | ✅ 1 | 0.45 / 0.32 | 1448 / 0 |
| 17 | ❌ excluded (> 25% epochs flagged) | 9 | 185 (118 / 58 / 9) | ❌ 25.7% | 1 | ✅ 1 | 3.22 / 4.03 | 548 / 1 |
| 18 | ✅ ok | 7 | 147 (49 / 95 / 3) | ✅ 22.6% | 0 | ✅ 1 | 0.67 / 0.78 | 621 / 0 |
| 19 | ✅ ok | 7 | 144 (31 / 56 / 57) | ✅ 24.2% | 0 | ✅ 2 | 1.14 / 1.17 | 434 / 0 |
| 20 | ✅ ok | 7 | 155 (101 / 54 / 0) | ✅ 17.6% | 2 | ✅ 2 | 3.06 / 3.17 | 19 / 0 |
| 21 | ✅ ok | 2 | 36 (22 / 14 / 0) | ✅ 10.0% | 0 | ✅ 1 | 1.69 / 1.84 | 114 / 0 |
| 22 | ✅ ok | 10 | 263 (144 / 106 / 13) | ✅ 6.1% | 0 | ✅ 1 | 1.25 / 2.61 | 805 / 0 |
| 23 | ✅ ok | 10 | 206 (50 / 49 / 107) | ✅ 8.8% | 54 | ✅ 2 | 1.17 / 1.39 | 864 / 32 |
| 24 | ✅ ok | 8 | 193 (96 / 46 / 51) | ✅ 12.3% | 0 | ✅ 0 | 1.50 / 2.74 | 2069 / 64 |
| 25 | ✅ ok | 8 | 208 (63 / 128 / 17) | ✅ 5.5% | 0 | ✅ 2 | 4.47 / 5.61 | 102 / 0 |
| 26 | ✅ ok | 8 | 175 (168 / 7 / 0) | ✅ 20.5% | 0 | ✅ 3 | 2.28 / 3.64 | 278 / 0 |
| 27 | ✅ ok | 9 | 207 (51 / 75 / 81) | ✅ 16.5% | 2 | ✅ 1 | 1.36 / 1.55 | 1251 / 58 |
| 28 | ✅ ok | 8 | 200 (117 / 19 / 64) | ✅ 7.0% | 5 | ✅ 3 | 1.51 / 1.76 | 120 / 0 |
| 29 | ✅ ok | 9 | 222 (203 / 12 / 7) | ✅ 11.2% | 0 | ✅ 2 | 2.02 / 2.86 | 764 / 153 |
| 30 | ✅ ok | 8 | 184 (96 / 72 / 16) | ✅ 15.6% | 2 | ✅ 2 | 4.95 / 5.10 | 11 / 0 |
| 31 | ❌ excluded (> 25% epochs flagged) | 8 | 138 (9 / 72 / 57) | ❌ 37.3% | 0 | ✅ 0 | 0.41 / 0.64 | 826 / 0 |
| 32 | ✅ ok | 10 | 236 (198 / 21 / 17) | ✅ 12.6% | 10 | ✅ 1 | 0.71 / 0.78 | 1837 / 445 |
| 33 | ✅ ok | 9 | 204 (150 / 48 / 6) | ✅ 18.4% | 0 | ✅ 1 | 1.07 / 0.91 | 754 / 0 |

</details>
<!-- participants-table:end -->

<details>
<summary><b>🔎 Participant 1 in detail (preview, not the study result)</b></summary>

Trained on 4 of participant 1's recordings and tested on the fifth, rotating through all five ([`score_one_person.py`](score_one_person.py)). 118 epochs kept (wake 38, N1 46, N2 34; 12 flagged by Autoreject). Full tables: [`results/preview_sub-01_scores.csv`](results/preview_sub-01_scores.csv), [`results/preview_sub-01_quality.csv`](results/preview_sub-01_quality.csv).

| Task | Model | Raw | Filtered | Cleaned (MNE) | Cleaned (refined) |
|---|---|:---:|:---:|:---:|:---:|
| Wake / N1 / N2 | Logistic regression | −0.03 | −0.06 | −0.01 | −0.04 |
| Wake / N1 / N2 | Gradient boosting | 0.10 | −0.08 | 0.01 | −0.11 |
| Wake vs N2 | Logistic regression | −0.11 | 0.09 | 0.03 | −0.10 |
| Wake vs N2 | Gradient boosting | 0.12 | −0.04 | 0.03 | 0.23 |

| Recording | INPS MNE (double counts) | INPS refined (double counts) | Bad channels | Epochs flagged |
|---|:---:|:---:|:---:|:---:|
| Rest 1 | 1.63 dB (54) | 1.37 dB (0) | Fp2 | 2 of 20 |
| Rest 2 | 0.10 dB (8) | 0.05 dB (0) | – | 3 of 20 |
| Sleep 1 | 0.99 dB (87) | 1.69 dB (0) | – | 5 of 30 |
| Sleep 2 | 1.34 dB (122) | 2.10 dB (0) | – | 1 of 30 |
| Sleep 3 | 0.88 dB (65) | 1.51 dB (0) | F8 | 1 of 30 |

Within participant 1 every arm stays near chance and the order of the arms changes between rows, so one person cannot separate them: about 90 training epochs for 134 features, very different stage mixes between recordings, and a hard case (in an earlier code test, wake vs N2 stayed at chance for them in both raw and cleaned data). The refined detector removed more heartbeat artefact in all three sleep recordings and never double-counted. In rest 2 both removed almost nothing and disagree on the heart rate (65 vs 80 bpm): that recording's ECG needs investigating.
</details>

## 🔬 Methods

<details>
<summary><b>Data</b></summary>

All 33 participants of [OpenNeuro ds003768](https://openneuro.org/datasets/ds003768/versions/1.0.13): 6,858 cleanly labelled 30-second epochs (wake 3,343, N1 2,148, N2 1,325, N3 42). N3 is too rare to model and is merged with N2. Epochs the dataset's expert scorer marked **uncertain or unscorable** (1.9%) are left out, using the study's own flags.
</details>

<details>
<summary><b>Pipeline, step by step</b></summary>

Only established EEG methods and the dataset's own information are used for cleaning and scoring.

1. **Scanner artefact:** average artefact subtraction locked to the R128 volume triggers, 21-volume sliding template (Allen, Josephs & Turner, 2000, *NeuroImage*).
2. **Heartbeat artefact:** average artefact subtraction locked to each heartbeat, 21-beat template (Allen et al., 1998, *NeuroImage*). Two detectors, compared as arms: MNE-Python's `find_ecg_events` (Gramfort et al., 2013), unmodified; and the same with timing refinement (beat placed at the 8–25 Hz ECG energy peak, at most one per 0.6 beat intervals). The refinement is this study's documented adaptation, not a published detector. Removal is skipped if the heart rate is outside 40–120 bpm (logged).
3. **Filter and resample:** 0.3–40 Hz, 250 Hz.
4. **Features (identical for every arm):** following common sleep-staging practice (e.g. Vallat & Walker, 2021), per 30-second epoch and per region (frontal, central, posterior, temporal): log and relative power in delta, theta, alpha, sigma and beta from Welch spectra (Welch, 1967), 95% spectral edge, theta/alpha ratio, Hjorth mobility and complexity (Hjorth, 1970); slow and fast eye-channel power. 67 features, plus a ±2-epoch context average. The ECG channel is never used as a feature.
5. **Quality checks and exclusions:** see below. Judged on the standard-cleaned (MNE) recording and applied identically to every arm.
6. **Tasks and models:** wake / N1 / N2 and wake vs N2; logistic regression on standardised features and gradient-boosted trees (Friedman, 2001), both with balanced class weights, in scikit-learn (Pedregosa et al., 2011). **Leave-one-person-out** cross-validation.
7. **Statistics:** Cohen's kappa (Cohen, 1960) against the expert for each person, coloured by the Landis & Koch (1977) bands; arms compared with paired Wilcoxon signed-rank tests (Wilcoxon, 1945) and bootstrap 95% confidence intervals (Efron, 1979) of the mean difference; a stratified-chance classifier gives the floor.
</details>

## 🩺 Quality checks

Every recording is checked at four levels ([`src/preprocessing/quality.py`](../../src/preprocessing/quality.py); summary by [`src/postprocessing/quality_report.py`](../../src/postprocessing/quality_report.py)):

| Level | What is checked | Method | Used for |
|---|---|---|---|
| 📁 **Files** | Size and MD5 checksum against OpenNeuro; 32 channels, ECG and EOG, regular scanner triggers; agreement with the dataset's BIDS metadata | Checksums; BIDS sidecar files | ✅/❌ |
| 🔌 **Channels** | Flat, abnormal-amplitude, poorly correlated and unpredictable channels | **PREP** (Bigdely-Shamlo et al., 2015) via PyPREP; its high-frequency criterion is not used (data low-passed at 40 Hz) | Recording excluded if > 3 of 30 channels are bad (10%, a common convention) |
| 🧩 **Epochs** | Peak-to-peak amplitude above a threshold learned from the recording | **Autoreject** global threshold (Jas et al., 2017) on the labelled 30-s epochs | Epoch excluded; person excluded if > 25% flagged (a common convention) |
| 💓 **Correction** | Heartbeat removal: **INPS**, power in 1-Hz windows at the first five heart-rate harmonics before vs after, in dB (Tong et al., 2001). Scanner removal: residual peak at the slice frequency and its harmonic | Published metrics | Reported; no pass/fail, because no published threshold exists |

Signal preservation uses the dataset's own labels: for each person, posterior alpha should be higher in wake than in N2, following evaluations that check a known physiological contrast survives cleaning (Abreu et al., 2016; Gallego-Rudolf et al., 2022). Reported for every arm.

> [!WARNING]
> **Metadata mismatch:** the dataset's BIDS metadata says the EEG is sampled at 250 Hz, but every file header and the data are 5,000 Hz. Recorded as an integrity finding; the files are used as they are.

> [!NOTE]
> **General-purpose ECG detectors fail on in-scanner ECG** ([`compare_qrs_detectors.py`](compare_qrs_detectors.py)). NeuroKit2's (Makowski et al., 2021) implementations of published clinical detectors (Pan & Tompkins, 1985; Hamilton, 2002; Elgendi et al., 2010; Engelse & Zeelenberg, 1979 modified by Lourenço et al., 2012; Christov, 2004) and a Teager-energy detector (Kim et al., 2004) reported 110–254 bpm or missed or double-counted hundreds of beats on participants 1 and 4. MNE's detector found the right rate (82 and 66 bpm) but double-counted 87 and 155 beats (7–14%); the refined version counted none double. The recording reference is FCz (from the metadata), which is why Fz and Cz look nearly flat.

<details>
<summary><b>🧪 Exploratory diagnostics (not used for scoring)</b></summary>

These use this study's own tests rather than established metrics, so they inform the method but never decide inclusion or results.

- [`data_accounting.py`](data_accounting.py): share of signal each step removes on participant 1: gradient subtraction 99.68% of raw power; the 0.3–40 Hz filter 12.8% of the rest (10.5% below 0.3 Hz, 2.3% above 40 Hz); heartbeat subtraction 19.9% (sigma band 57%); cropping 3.5% of recording time.
- [`overcorrection_check.py`](overcorrection_check.py): the same heartbeat subtraction at heartbeat-like times not locked to the heart removes 3.3–5.1% of band power, close to the method's theoretical 1/21 (4.8%), against 22–57% at real heartbeats.
- [`validate_obs.py`](validate_obs.py): optimal basis sets (4 components) raise heartbeat removal (INPS 6.79 vs 1.69 dB) but remove 69.6% of 0.5–30 Hz power; at times not locked to the heart they still remove 75% of delta and 32% of theta, against 4–5% for average subtraction. Sleep slow waves last about one heartbeat and are absorbed into the basis, so OBS is not used.
- [`obs_one_person.py`](obs_one_person.py) (amendment 4, exploratory): participant 1 rebuilt with OBS and scored like the other arms ([`results/obs_staging_sub-01.csv`](results/obs_staging_sub-01.csv)). OBS removed 2–5× more heartbeat artefact in every recording (INPS 1.7–6.8 dB vs 0.1–2.1 dB), but staging did not improve. Wake vs N2 was below chance for both OBS arms (kappa −0.17 to −0.10), and no arm beats chance reliably for this person (about 70–120 epochs; kappa standard error ≈ 0.1). No evidence that OBS helps; the amendment-2 decision stands.
- [`validate_stages.py`](validate_stages.py): notch, spline interpolation and re-reference steps on participant 1 (pre-registration amendment 1).
- [`signal_preservation.py`](signal_preservation.py): the cleaned spectrum keeps the shape of the 24 s recorded before scanning between 0.5 and 15 Hz. That stretch already contains unmarked scanner warm-up (16.7 Hz), so it is an imperfect reference. A 38.5 Hz peak is present before scanning too (scanner-room equipment), and 3 and 6 Hz peaks appear only during scanning.

![Pre-scan vs cleaned scanning spectrum](results/signal_preservation_sub-01.png)
</details>

## 📝 Corrections log

<details>
<summary><b>Every fix and every change to the plan, dated (all before any 33-person results)</b></summary>

- **In-place filtering bug (fixed 22 Oct 2026).** MNE's `RawArray` does not copy its input and `filter()` works in place, so building the *filtered* arm altered the data the *cleaned* arm was built from. Fixed with explicit copies. Participant 1's headline numbers barely moved (sigma 7.2 → 7.1 µV²/Hz; ratios unchanged), but all features are rebuilt.
- **Heartbeat double counting (fixed).** The first detector counted T-waves as beats in some recordings (participant 4: 106 bpm instead of 66).
- **Custom quality rules replaced (22 Oct 2026).** The first version used this study's own tests (random-timing residual, surrogate brain loss, a 2-of-3-window epoch rule). They were replaced by established methods (INPS, standard Autoreject, PREP) and the dataset's own labels, after quality checks on a few recordings of participants 1–4 and before any classification results.
- **Analysis plan revised before results.** After a code test on 4–5 people, logistic regression and the wake-vs-N2 task were added and per-person feature scaling moved to a sensitivity analysis (`--norm`), because people's stage mixes differ hugely (one is 96% wake, another 76% N2).
- **Two dataset file problems (handled 22 Oct 2026).** sub-16 sleep run 1 has no `.eeg` data file on OpenNeuro (header and markers only); the build crashed on the missing download and now skips such runs, logged as "file missing from dataset". sub-16 rest run 1's header names its data file `rsub-16_…` (a typo); the local copy of the header is pointed at the real file and the fix is recorded in the quality table (`header_datafile_fixed`); the data file itself is unchanged and its MD5 is still checked.
- **Label-file typo (handled 22 Oct 2026, before sub-32 was built).** In `sub-32-sleep-stage.tsv`, line 69 (sleep run 1, 810 s) separates the time and the stage with a space instead of a tab. The reader now accepts that one pattern; all other 32 label files were checked to parse identically.
- **Event channels (fixed 22 Oct 2026, before any event-set results).** The right mastoid (TP10) is bad in 40 of the first 149 recordings, and event detection had used it for the left-hemisphere derivations. Events now use the AASM recommended derivations (F4–M1, C4–M1, O2–M1), with the backups only when a recommended electrode is bad (amendment 7); all event features are recomputed.
- **Recordings with no scorable epochs (handled 22 Oct 2026).** Every epoch of sub-23 rest run 1 is marked "W (uncertain)" by the expert, so after the uncertain epochs are dropped nothing is left, and the quality step crashed on an empty recording. Such recordings are now skipped and logged as "no expert-scored epochs" (after the checksum and header checks); no data changes.
</details>

> [!TIP]
> The analysis plan, exclusions and tests are fixed in [PREREGISTRATION.md](PREREGISTRATION.md), written before the full results.

## 📚 References

Full citations with DOIs for every method, metric, dataset and software package: **[REFERENCES.md](../../REFERENCES.md)**. Optimal basis sets (Niazy et al., 2005) were tested and not adopted: on participant 1 they removed 75% of delta power even at times not locked to the heart ([`validate_obs.py`](validate_obs.py); pre-registration amendment 2).

## ⚠️ Limitations

- Narrow residual artefact peaks remain after cleaning (20–48 Hz; see the spectrum).
- The artefact templates include the current volume or heartbeat, which subtracts about 1/21 (5%) of that segment's own brain signal.
- Cleaning removes any brain response genuinely locked to the heartbeat (heartbeat-evoked potentials, a few µV); irrelevant for sleep staging, relevant for body–brain research.
- Naps in a scanner contain almost no deep sleep, and only 16 of 33 people have 10 or more minutes of N2.
- 33 people is a small sample; results are reported per person with confidence intervals, not only as one pooled number.

## ▶️ Reproduce

<details>
<summary><b>Commands</b></summary>

```bash
python studies/01-preprocessing-ablation/build_dataset.py     # download, clean (4 arms), quality-check, extract features (~10 h)
python src/postprocessing/quality_report.py studies/01-preprocessing-ablation/results   # quality tables + figure
python studies/01-preprocessing-ablation/compare_arms.py      # leave-one-person-out comparison -> results/
python studies/01-preprocessing-ablation/participant_table.py # the all-participants tables in this README
python src/postprocessing/study01_banner.py                   # this README's banner, from real data
python studies/01-preprocessing-ablation/compare_qrs_detectors.py <recording.vhdr> [...]
```
</details>
