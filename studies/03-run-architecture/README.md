# Study 03 · Sleep across the five runs of a session

**Question.** Each ds003768 session runs in a fixed order: rest run 1 (10 min), a visual-motor adaptation task, rest run 2 (10 min), then 15-min sleep runs (dataset README). How do the amount, depth and onset of sleep change across **rest 1, rest 2, sleep 1, sleep 2 and sleep 3**, for the group and for each participant? Pre-registered in [PREREGISTRATION.md](PREREGISTRATION.md) before any per-run summary was computed; the expert labels had been seen in earlier studies, so this is not a blind analysis.

**Data.** The dataset's expert 30-s stage labels; no EEG is analysed. W, N1, N2 and N3 are kept separate; epochs the expert marked uncertain or unscorable are excluded from every denominator.

**Participants (amendment 1, post hoc).** The **14 qualified participants**: passed study 01's quality rules and awake for less than 50% of usable epochs (01, 04, 07, 09, 11, 14, 15, 16, 18, 19, 23, 24, 25, 27). Participant 23 has no scored epochs in rest 1 and sleep 2, so **13** enter the tests. The original plan used all 29 who passed the quality rules (26 testable); those results are reported [below](#comparison-original-plan-26-participants) for comparison.

> [!WARNING]
> **The qualification rule selects on the outcome.** It keeps people who slept for most of the session, which is close to what this study measures. In this group sleep is near ceiling in most runs, and the people who stayed awake until the later runs are excluded. Results here describe the qualified sleepers; they are not an independent test of the pre-registered hypotheses.

## Results

> [!IMPORTANT]
> **In the qualified participants, sleep did not change significantly across the five runs.** They were asleep for most of every run (median 60–90%), with no significant difference between runs (Friedman p = 0.34, Kendall's W = 0.09) and no trend with run order (Page p = 0.21). No secondary measure survived correction. One pattern recurred without reaching significance: **sleep 1 had the slowest sleep onset** (median 3 min, against 30 s or less in every other run; uncorrected p = 0.034, Holm p = 0.10). In the larger original-plan group (26 participants), sleep did increase across runs, carried by sleep 3; that increase comes mostly from participants the qualification rule excludes.

![Every qualified participant's hypnogram across the five runs](results/hypnograms.png)

![Qualified participants: stage make-up, sleep share, sleep-onset latency, exploratory groups, rest vs sleep](results/run_overview.png)

### Pre-registered tests (qualified, n = 13)

| Measure | rest 1 | rest 2 | sleep 1 | sleep 2 | sleep 3 | Test | p | Holm p | Conclusion |
|---|:---:|:---:|:---:|:---:|:---:|---|:---:|:---:|---|
| Sleep share (H1) | 0.85 | 0.73 | 0.60 | 0.80 | 0.90 | Friedman | 0.34 | — | No difference |
| Sleep share, ordered (H2) | | | | | | Page's L | 0.21 | — | No trend |
| N2 share | 0.20 | 0.05 | 0.00 | 0.00 | 0.20 | Friedman | 0.045 | 0.10 | Not significant after correction |
| Sleep-onset latency (min) | 0.5 | 0.0 | 3.0 | 0.5 | 0.0 | Friedman | 0.034 | 0.10 | Not significant after correction |
| Stage shifts per hour | 36 | 24 | 24 | 32 | 24 | Friedman | 0.67 | 0.67 | No difference |

Values are medians. A run without sleep is assigned its full length as the latency (10 or 15 min). Adjacent-run follow-ups were not run because no test was significant.

### Descriptive results (qualified)

- **Sleep in every run.** Participants who slept at all: 12 of 13 with scored data in rest 1, 13 of 14 in rest 2, 12 of 14 in sleep 1, 12 of 13 in sleep 2 and 14 of 14 in sleep 3.
- **The "rest" runs were mostly sleep.** The median qualified participant was asleep for 85% of rest 1, the run recorded *before* the task, often reaching N2. For these participants the rest runs are not an awake baseline.
- **Depth.** N1 was the most common sleep stage in every run (mean 41–53%). N3 appeared only in sleep 3, in participants 04, 23 and 27.
- **Fragmentation.** Median 24–36 stage shifts per hour, with no difference between runs.
- **Rest and sleep runs were unrelated within this group** (Spearman ρ = 0.24, p = 0.40), unlike the larger group, where the restriction of range is smaller.

### Pattern of each participant (descriptive)

Sleep share per run (share of scored epochs in N1, N2 or N3):

| Participant | rest 1 | rest 2 | sleep 1 | sleep 2 | sleep 3 | Pattern |
|:---:|:---:|:---:|:---:|:---:|:---:|---|
| 07 | 0.85 | 1.00 | 1.00 | 1.00 | 1.00 | Asleep throughout; N2 builds in sleep 3 |
| 16 | 1.00 | 1.00 | 1.00 | 1.00 | 0.97 | Asleep throughout, much N2 from rest 1 |
| 14 | 0.35 | 1.00 | 0.87 | 1.00 | 1.00 | Partly awake in rest 1, then asleep (mostly N1) |
| 19 | 0.50 | 0.00 | 1.00 | 0.90 | 0.90 | Fully awake in rest 2, then asleep with N2 |
| 04 | 0.40 | 0.25 | 0.60 | 0.57 | 0.93 | Sleep builds; deepest in sleep 3 (N2, ends in N3) |
| 25 | 0.95 | 1.00 | 0.57 | 0.80 | 0.87 | Asleep, with a dip at sleep 1 |
| 27 | 0.95 | 0.50 | 0.47 | 0.80 | 1.00 | Dip at rest 2–sleep 1; N2 then N3 in sleep 3 |
| 09 | 0.85 | 0.39 | 0.13 | 0.50 | 0.80 | U-shape: lowest in sleep 1 |
| 15 | 0.85 | 0.65 | 0.23 | 0.43 | 0.87 | U-shape: lowest in sleep 1 |
| 01 | 0.95 | 0.25 | 0.90 | 0.60 | 0.67 | Asleep (N2) before the task, mostly awake in rest 2 |
| 18 | 1.00 | 0.75 | 0.87 | 0.47 | 0.53 | Declining; more wake in sleep 2–3 |
| 11 | 0.05 | 0.73 | 0.00 | 0.83 | 0.93 | Alternating: awake in rest 1 and sleep 1 |
| 24 | 0.00 | 1.00 | 0.00 | 0.00 | 0.27 | Slept (N2) only in rest 2 |
| 23 | — | 0.05 | 0.67 | — | 1.00 | Incomplete; sleep 3 scored N3 throughout (see below) |

Recurring patterns across individuals:

- **A dip at sleep 1.** Sleep 1 had less sleep than rest 2 in 7 of 13 participants (09, 11, 14, 15, 24, 25, 27) and the slowest onset of the session at the median, although neither difference was significant. The dataset does not describe what happened between rest 2 and sleep 1.
- **Sleep 3 is the deepest run.** All 14 slept in sleep 3, and every N3 epoch in the five runs occurred there.
- **Exploratory clustering adds little.** Ward clustering chose two groups (silhouette 0.35, weak structure; Rousseeuw, 1987): 11 participants asleep in most runs and 2 (11, 24) awake in rest 1 and sleep 1. With 13 people and near-ceiling sleep, the individual table above is more informative.

**Participant 23.** Sleep 3 is scored N3 in all 29 scored epochs, which is 29 of the 42 N3 epochs in the whole dataset. It follows a sleep 2 with no scorable epochs. This record should be checked against the EEG before any N3 analysis relies on it.

### Comparison: original plan (26 participants)

In the 26 testable participants who passed the quality rules, both hypotheses were supported. Sleep share differed across runs (Friedman p = 0.005, W = 0.14) and rose with run order (Page p = 0.003): medians 0.39, 0.32, 0.27, 0.52 and 0.80. The only significant adjacent step was **sleep 2 → sleep 3**: more sleep (18 of 26, Holm p = 0.011), more N2 (16 of 26, Holm p = 0.010) and faster onset (18 of 26, Holm p = 0.035). N2 share and sleep-onset latency differed across runs (both Holm p = 0.002), and stage shifts did not (p = 0.26). Sleep 1 again had the slowest onset (median 6.8 min), rising from rest 2 in 16 of 22 participants with a change (Holm p = 0.053). Sleep in the rest runs correlated with sleep in the sleep runs (ρ = 0.43, p = 0.026). Ignoring the quality exclusions (30 participants) gave the same conclusions. Figures: [`results/quality_passed/`](results/quality_passed).

The two analyses agree once the selection is taken into account. The qualified participants were already asleep for most of the session, so there was little room for sleep to rise. The run-order effect in the larger group is carried by participants who stayed mostly awake until the later runs, and the qualification rule excludes them.

### Interpretation and limitations

- **Selection.** The qualification rule overlaps with the outcome (see the warning above). The null result here means "no further increase among people who already slept", not "no effect of run order".
- **Small sample.** With 13 participants and a ceiling, only large differences could be detected.
- **Order is confounded with time.** The run order is fixed, so run type, time of day and time in the scanner cannot be separated.
- **Expert labels only.** All measures depend on a single expert's scoring.

### Corrections

The first published version of this study counted a run with no scored epochs (participant 23, rest 1 and sleep 2) as a run without sleep, so the participant entered the sleep-onset latency tests with invented latencies (n = 27 instead of 26). Such runs are now treated as missing. In the 26-participant analysis, the latency medians changed slightly (for example, sleep 1 from 6.5 to 6.8 min); the Friedman test stayed at Holm p = 0.002, and the sleep 2 → sleep 3 latency step changed from Holm p = 0.020 to 0.035. No conclusion changed.

## Reproduce

```bash
python studies/03-run-architecture/run_architecture.py                    # qualified (primary) -> results/
python studies/03-run-architecture/run_architecture.py --group quality    # original plan -> results/quality_passed/
python studies/03-run-architecture/run_architecture.py --group all        # sensitivity -> results/sensitivity_all/
python studies/03-run-architecture/figures_architecture.py [--group quality]
```

## References

- Berry, R. B., et al. *The AASM Manual for the Scoring of Sleep and Associated Events*. American Academy of Sleep Medicine.
- Friedman, M. (1937). The use of ranks to avoid the assumption of normality implicit in the analysis of variance. *Journal of the American Statistical Association*, 32(200), 675–701. https://doi.org/10.1080/01621459.1937.10503522
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, 6(2), 65–70.
- Kendall, M. G., & Babington Smith, B. (1939). The problem of *m* rankings. *The Annals of Mathematical Statistics*, 10(3), 275–287. https://doi.org/10.1214/aoms/1177732186
- Page, E. B. (1963). Ordered hypotheses for multiple treatments: a significance test for linear ranks. *Journal of the American Statistical Association*, 58(301), 216–230. https://doi.org/10.1080/01621459.1963.10500843
- Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53–65. https://doi.org/10.1016/0377-0427(87)90125-7
- Spearman, C. (1904). The proof and measurement of association between two things. *The American Journal of Psychology*, 15(1), 72–101. https://doi.org/10.2307/1412159
- Tagliazucchi, E., & Laufs, H. (2014). Decoding wakefulness levels from typical fMRI resting-state data reveals reliable drifts between wakefulness and sleep. *Neuron*, 82(3), 695–708. https://doi.org/10.1016/j.neuron.2014.03.020
- Ward, J. H. (1963). Hierarchical grouping to optimize an objective function. *Journal of the American Statistical Association*, 58(301), 236–244. https://doi.org/10.1080/01621459.1963.10500845
- Wilcoxon, F. (1945). Individual comparisons by ranking methods. *Biometrics Bulletin*, 1(6), 80–83. https://doi.org/10.2307/3001968
