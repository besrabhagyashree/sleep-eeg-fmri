# Study 03 · Pre-registration: sleep across the five runs of a session

**Author:** Bhagyashree Besra · **Registered:** 2026-10-23 16:56 IST, before any per-run summary in this plan was computed.

## Question

Each ds003768 session runs in a fixed order: rest run 1 (10 min), a visual-motor adaptation task, rest run 2 (10 min), then 15-min sleep runs (dataset README). How does the amount, depth and stability of sleep change across **rest 1, rest 2, sleep 1, sleep 2 and sleep 3**, for the group and for each participant?

## Prior exposure (honest disclosure)

The expert labels were seen in earlier studies: the share of wake in the two rest runs (study 02 screening) and the stage sequences pooled across runs (study 01 transitions). Per-run summaries across all five runs, the latencies and the tests below have not been computed. The tests are therefore pre-specified, but the data are not unseen; results are reported with that caveat.

## Data

- **Labels:** the dataset's expert 30-s stage labels (`sourcedata/sub-XX-sleep-stage.tsv`). No EEG is analysed in this study.
- **Stages:** W, N1 (`1`), N2 (`2`) and N3 (`3`) are kept separate here (studies 01–02 merged N3 into N2 for classification). Epochs marked uncertain or unscorable are excluded from every denominator, and their count is reported per run.
- **Runs:** `task-rest_run-1`, `task-rest_run-2`, `task-sleep_run-1`, `-2`, `-3`. Later sleep runs (4–8) exist for fewer participants and are not analysed.
- **Participants:** the 29 who passed study 01's quality rules (03, 13, 17 and 31 excluded), restricted to those with expert labels for all five runs. **Sensitivity:** all participants with five labelled runs, quality exclusions ignored (the labels do not depend on EEG quality).

## Measures (per participant, per run)

1. **Sleep share** (primary): (N1 + N2 + N3) / scored epochs.
2. Stage shares: W, N1, N2, N3.
3. **Sleep-onset latency:** time from run start to the first epoch of any sleep stage (AASM definition of sleep onset; Berry et al.). A run without sleep is assigned the run length (censored; rank tests treat these as ties at the maximum).
4. **Latency to N2:** first N2 epoch, censored the same way.
5. **Stage shifts per hour:** changes between consecutive scored epochs to a different stage, per hour of scored time.
6. **Awakenings per hour:** sleep → W changes, per hour of scored time.
7. **Deepest stage reached.**

Rates and shares are used because rest runs (20 epochs) and sleep runs (30 epochs) differ in length.

## Hypotheses and tests

- **H1 (primary).** Sleep share differs across the five runs. Friedman test (Friedman, 1937); effect size Kendall's W (Kendall & Babington Smith, 1939). α = 0.05.
- **H2.** Sleep share increases with run order (rest 1 < rest 2 < sleep 1 < sleep 2 < sleep 3). Page's L trend test (Page, 1963). Rationale: the probability of sleep in the scanner grows with time spent lying still (Tagliazucchi & Laufs, 2014), and the sleep runs are the sleep opportunity.
- **Secondary (Holm-corrected as one family).** Friedman tests on N2 share, sleep-onset latency and stage shifts per hour.
- **Follow-up for any significant Friedman test.** Wilcoxon signed-rank tests on the four adjacent run pairs (rest 1→rest 2, rest 2→sleep 1, sleep 1→sleep 2, sleep 2→sleep 3), Holm-corrected within each measure.
- **Trait consistency.** Spearman correlation across participants between mean sleep share in the rest runs and in the sleep runs (do people who doze during rest also sleep more in the sleep runs?).

## Per-participant patterns (descriptive / exploratory)

- A hypnogram for every participant across the five runs, plus a per-run table of the measures above.
- Each participant's direction across runs: Spearman ρ between run order and sleep share (descriptive only; five points per person, no per-person p-values).
- **Exploratory grouping:** Ward hierarchical clustering (Ward, 1963) of the five-run sleep-share profiles, number of clusters (2–5) chosen by mean silhouette width (Rousseeuw, 1987). Clusters are descriptive and are not tested.

## What would count as a finding

H1 or H2 significant at α = 0.05. Secondary measures count only after Holm correction. Clusters and per-person directions are descriptive and are not claims.

## References

- Berry, R. B., et al. *The AASM Manual for the Scoring of Sleep and Associated Events*. American Academy of Sleep Medicine.
- Friedman, M. (1937). The use of ranks to avoid the assumption of normality implicit in the analysis of variance. *Journal of the American Statistical Association*, 32(200), 675–701. https://doi.org/10.1080/01621459.1937.10503522
- Kendall, M. G., & Babington Smith, B. (1939). The problem of *m* rankings. *The Annals of Mathematical Statistics*, 10(3), 275–287. https://doi.org/10.1214/aoms/1177732186
- Page, E. B. (1963). Ordered hypotheses for multiple treatments: a significance test for linear ranks. *Journal of the American Statistical Association*, 58(301), 216–230. https://doi.org/10.1080/01621459.1963.10500843
- Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53–65. https://doi.org/10.1016/0377-0427(87)90125-7
- Tagliazucchi, E., & Laufs, H. (2014). Decoding wakefulness levels from typical fMRI resting-state data reveals reliable drifts between wakefulness and sleep. *Neuron*, 82(3), 695–708. https://doi.org/10.1016/j.neuron.2014.03.020
- Ward, J. H. (1963). Hierarchical grouping to optimize an objective function. *Journal of the American Statistical Association*, 58(301), 236–244. https://doi.org/10.1080/01621459.1963.10500845
