# Study 04 · Pre-registration: multi-site replication of study 01

**Author:** Bhagyashree Besra · **Registered:** 2026-10-27 13:45 IST, before any EEG from the new datasets was processed. The new datasets' stage labels have been inventoried (counts per stage, scanner-on/off counts, label format); no EEG feature, classifier output or quality metric has been computed.

## Question

Do study 01's findings hold in independent simultaneous EEG-fMRI sleep data from other sites, scanners and scorers? In particular, does artefact correction improve automated sleep staging, and if not, is any effect small enough to be called negligible?

## Datasets

| Dataset | Site | Participants | Recording | EEG available | Labels |
|---|---|:---:|---|---|---|
| ds003768 (study 01) | Penn State | 29 analysed | rest + sleep runs, 32 ch, 5 kHz | raw | expert, 30-s epochs |
| **ds005127** (Moehlman et al., 2019) | NIH (NINDS) | 16 | overnight, 1–2 nights, 63 EEG + ECG + EMG, 5 kHz, TR 3 s | raw | expert AASM scoring of in-scanner EEG, 30-s epochs, W/N1/N2/N3/REM |
| **ds003574** (Sterpenich et al., 2021) | Geneva | 18 | nap of 1–2 h, 64 ch, 500 Hz, TR 2.1 s | **cleaned only** (authors' gradient + heartbeat correction) | hypnogram per fMRI volume |

**Label decoding.** ds005127: the dataset FAQ's codebook (6 = W, 4 = N1, 3 = N2, 2 = N3, 4 with REM flag = REM, 0 = unscorable). ds003574: codes 0–3 = W, N1, N2, N3, inferred from the data before this registration (slow-wave and delta power rise monotonically from 0 to 3; code 3 occurs in exactly the 13 participants the dataset lists as reaching N3). Its per-volume labels change only at a fixed 30-s phase within each participant, so the original 30-s epochs are reconstructed from that phase; each epoch takes the label of its volumes, and epochs whose volumes disagree are excluded.

## Methods (identical to study 01 unless stated)

- **Arms (ds005127):** raw, filtered, cleaned (MNE), cleaned (refined), exactly as study 01 section 4. Processing is done one channel at a time and one run at a time (memory and disk only; the arithmetic is unchanged).
- **ds003574:** cleaned arm only (the dataset's own cleaning), then 0.3–40 Hz and 250 Hz as in the other arms.
- **Epochs (ds005127):** only epochs scored with the MRI on for the whole epoch (`MRIon` = 1) and fully inside the volume-trigger span. REM and unscorable epochs are excluded from staging; N3 is merged into N2, as in study 01.
- **Features:** the same 67 spectral features. ds005127 has no F7/F8, so the frontal group uses its remaining electrodes; its E1 channel is used as the EOG channel. Cross-site analyses use EEG features only (EOG excluded), because the eye channels differ between sites.
- **Exclusions:** study 01 rules 1–5. Rule 4 (more than 3 of 30 scalp channels bad, i.e. 10%) is applied proportionally: more than 10% of scalp channels.
- **Classification:** leave-one-participant-out within ds005127 (both nights of a participant held out together); logistic regression (primary) and gradient boosting, as in study 01.

## Hypotheses and tests

- **H1 (primary, independent replication).** In ds005127, per-participant three-class κ is higher for cleaned (MNE) than raw. Two-sided Wilcoxon signed-rank, α = 0.05, logistic regression; mean difference with bootstrap 95% CI.
- **H1-equivalence.** Two one-sided tests (TOST; Lakens, 2017) on the same per-participant differences, equivalence bounds ±0.15 κ, α = 0.05 each. Possible conclusions: improvement (H1 significant), negligible effect (TOST significant), or inconclusive (neither).
- **H2 (pooled).** The same contrast on ds003768 + ds005127 participants together (Wilcoxon, plus TOST ±0.15). ds003768's values were already reported in study 01, so H2 is not blind; H1 is the confirmatory test.
- **H3 (cardiac confound).** Study 01 amendment 5 method in ds005127: within expert stage, Spearman correlation between heart rate and predicted N2, raw arm; Wilcoxon of per-participant correlations against 0.
- **H4 (slow-wave validity).** In ds005127 and ds003574 (cleaned), per-participant slow-wave density (YASA `sw_detect`, study 01 amendment 6 settings) is higher in N2 than in W (Wilcoxon).
- **Secondary (exploratory):** gradient boosting for H1/H2; leave-one-site-out generalisation of the cleaned arm (train on two sites, test on the third, EEG features only); scanner-on vs scanner-off spectra within ds005127 nights; descriptive N3 and REM.

Power, stated in advance: with 15–16 participants, H1 has 80% power only for differences of about 0.15 κ or more (study 01's spread). TOST at ±0.15 needs about 40 participants at study 01's spread, so H1-equivalence is likely to be inconclusive in ds005127 alone; H2 (about 45 participants) is the better-powered test.

## Pilot (before the full run)

A pilot batch of about one hour processes a few ds005127 participants end to end, one at a time, to validate trigger alignment, label alignment, memory use and cleaning quality. **During the pilot only processing outputs are inspected:** quality metrics (file checks, bad channels, rejected epochs, heart rate, INPS, residual slice peak), stage counts and feature completeness. No classifier is trained and no hypothesis test is run until the full sample is processed. Pilot participants are included in the final analysis. If the pilot shows a processing error, the fix is applied to every participant and logged here as an amendment.

## References

- Lakens, D. (2017). Equivalence tests: a practical primer for *t* tests, correlations, and meta-analyses. *Social Psychological and Personality Science*, 8(4), 355–362. https://doi.org/10.1177/1948550617697177
- Moehlman, T. M., de Zwart, J. A., Chappel-Farley, M. G., Liu, X., et al. (2019). All-night functional magnetic resonance imaging sleep studies. *Journal of Neuroscience Methods*, 316, 83–98. https://doi.org/10.1016/j.jneumeth.2018.09.019
- Sterpenich, V., van Schie, M. K. M., Catsiyannis, M., et al. (2021). Reward biases spontaneous neural reactivation during sleep. *Nature Communications*, 12, 4162. https://doi.org/10.1038/s41467-021-24357-5
- Study 01 methods and their references: [`../01-preprocessing-ablation/PREREGISTRATION.md`](../01-preprocessing-ablation/PREREGISTRATION.md).

## Amendment 1 · pilot findings

**Added:** 2026-10-27 16:38 IST, after the pilot and before any classifier was trained or any hypothesis tested.

**Pilot participants:** ds005127 sub-00002 and sub-00067 (3 runs planned for sub-00040 were not started).

**Confirmed:** each row of a scoring file is the 30-s epoch starting at row × 30 s from the start of the EEG file; R128 volume triggers every 3.0 s; channel scaling read from the file matches MNE's reader; all file checksums pass. A run whose epochs are all marked unscorable by the expert is skipped under rule 1 (sub-00002, run 2: 113 of 113 unscorable).

**Processing fixes (no change to methods):** the live status file no longer blocks the pipeline when it is being read; raw files are deleted from the correct folder after each run; the next run downloads while the current one is processed; runs skipped by a rule count as handled in the progress counter.

**Open issue before the full run.** Heartbeat (ballistocardiogram) removal was effective in sub-00002 (INPS 3.9 dB) but weak in sub-00067 (median 0.7 dB; run 5 −0.9 dB, with 31% of beats double-counted by MNE's detector). This will be investigated against the dataset's own physiological recordings (`derivatives/physio_prepro`) before the full run. Any change of method will be a published one, applied to every participant, and registered here as amendment 2 before the full run starts. Pilot outputs remain limited to processing quality; no staging accuracy has been computed.
