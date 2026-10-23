# Study 02 · Alpha rhythm before and after a visual-motor task

**Question.** In OpenNeuro ds003768, each session has two 10-minute resting-state runs, the first before and the second after a visual-motor adaptation task (dataset README; task from Albouy et al., 2012). Does the individual alpha frequency (IAF) differ between them? Pre-registered in [PREREGISTRATION.md](PREREGISTRATION.md) before any rest-run alpha measure was computed.

**Data.** The 29 participants analysed in study 01; artefact-corrected rest runs; expert-scored wake epochs not rejected by Autoreject; posterior electrodes (O1, O2, Oz, P3, P4, Pz, P7, P8). Participants needed at least 6 such epochs (3 min) in both runs.

## Results

> [!IMPORTANT]
> **Primary hypothesis inconclusive.** Peak alpha frequency did not differ between the rest runs (median change 0.0 Hz, 4 higher / 4 lower / 4 unchanged, p = 1.0, n = 12). In exploratory analyses, **alpha power was higher after the task** (12 of 13 participants, p < 0.001; aperiodic-adjusted peak power 11 of 13, p = 0.010). Because the design has no control condition, this increase cannot be attributed to the task rather than to time spent in the scanner or changes in vigilance.

**Sample.** Only 13 of 29 participants had at least 3 minutes of usable wake in both runs: many participants were drowsy or asleep during the rest runs, especially the second (median wake share 0.50 in run 1, 0.75 in run 2; paired difference not significant, p = 0.42). A peak alpha frequency could be estimated in both runs for 12.

### Primary (pre-registered)

| Measure | Median before | Median after | Mean change [95% CI] | Higher / lower | p | Conclusion |
|---|:---:|:---:|:---:|:---:|:---:|---|
| Peak alpha frequency (Corcoran et al., 2018) | 9.88 Hz | 9.50 Hz | +0.31 Hz [−0.10, 1.02] | 4 / 4 | 1.0 | Inconclusive |

The positive mean reflects one participant (21: 8.0 → 12.0 Hz, estimated from 9 and 13 wake epochs); the median change was 0.0 Hz, and the other 11 participants changed by at most 0.25 Hz, the method's frequency resolution (4 not at all).

### Secondary (exploratory, uncorrected)

| Measure | n | Median before | Median after | Mean change [95% CI] | Higher / lower | p |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Alpha centre of gravity (Corcoran et al., 2018) | 12 | 9.63 Hz | 9.50 Hz | +0.23 Hz [0.04, 0.42] | 7 / 2 | 0.086 |
| FOOOF alpha centre frequency (Donoghue et al., 2020) | 13 | 10.67 Hz | 10.04 Hz | −0.31 Hz [−1.26, 0.57] | 6 / 7 | 0.74 |
| **Alpha power, log10 µV², 8–12 Hz** | 13 | 2.12 | 2.29 | **+0.15 [0.09, 0.22]** | **12 / 1** | **< 0.001** |
| **FOOOF aperiodic-adjusted alpha peak power** | 13 | 1.27 | 1.30 | **+0.11 [0.04, 0.19]** | **11 / 2** | **0.010** |
| FOOOF aperiodic exponent | 13 | 1.90 | 1.93 | −0.02 [−0.12, 0.07] | 9 / 4 | 0.68 |
| Share of rest run scored wake | 29 | 0.50 | 0.75 | +0.07 [−0.12, 0.24] | 14 / 9 | 0.42 |
| Peak alpha frequency, equal epochs per run (sensitivity) | 12 | 9.75 Hz | 10.13 Hz | +0.50 Hz [−0.13, 1.33] | 4 / 5 | 0.84 |

Alpha power rose by 0.15 log units (about 1.4-fold) after the task, consistently across participants; the increase in alpha power above the aperiodic background indicates that it was not a broadband shift. The power result (p < 0.001) would survive Bonferroni correction across the eight secondary tests (adjusted p ≈ 0.004); the aperiodic-adjusted result would not (≈ 0.08). Alpha frequency measures showed no consistent change.

### Interpretation and limitations

- **No control condition.** Higher alpha power in the second rest run is compatible with an effect of visual-motor learning but equally with time in the scanner, adaptation to the environment or relaxation. A design with a control task or a second baseline would be needed to attribute it.
- **Vigilance.** Analyses were restricted to expert-scored wake, but alpha power is sensitive to drowsiness within wake; the second rest run was not wakefulness-matched beyond the stage labels.
- **Small sample.** Only 12–13 of 29 participants had enough wake in both runs, because many fell asleep during rest.
- **Eyes open or closed** is not documented in the dataset.
- **Resolution.** Peak frequency is estimated on a 0.25 Hz grid, so changes smaller than this cannot be resolved.

## Reproduce

```bash
python studies/02-alpha-before-after/run_alpha.py   # -> results/alpha_per_participant.csv, results/summary.json
```

Methods code: [`src/methods/alpha.py`](../../src/methods/alpha.py); tests: [`tests/test_alpha.py`](../../tests/test_alpha.py).
