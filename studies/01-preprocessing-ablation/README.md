# Study 01: Does preprocessing matter?

EEG recorded during fMRI is buried under scanner and heartbeat artefacts hundreds of times larger than brain activity. Labs routinely remove them before analysis, but how much does that cleaning change what a sleep-staging model can learn?

This study answers that with an **ablation**: the same classifier, trained and tested on the same people and expert labels, using three versions of the same EEG.

| Arm | EEG used |
|---|---|
| **raw** | Straight from the dataset: 5 kHz, nothing removed or filtered |
| **filtered** | 0.3–40 Hz filter, 250 Hz, no artefact removal |
| **cleaned** | Scanner (gradient) and heartbeat (ballistocardiogram) artefacts removed, then the same filter |

## Data

All 33 participants of OpenNeuro ds003768: 6,858 cleanly labelled 30-second epochs (wake 3,343, N1 2,148, N2 1,325, N3 42). N3 is too rare to model and is merged with N2; epochs marked uncertain or unscorable (1.9%) are left out.

## Methods

1. **Scanner artefact:** average artefact subtraction locked to the R128 volume triggers, 21-volume sliding template (Allen, Josephs & Turner, 2000, *NeuroImage*).
2. **Heartbeat artefact:** R-peaks found in the ECG channel, then average artefact subtraction locked to each beat, 21-beat template (Allen et al., 1998, *NeuroImage*). Skipped for a recording if the detected heart rate is outside 40–120 bpm (logged).
3. **Filter and resample:** 0.3–40 Hz, 250 Hz.
4. **Features (identical for every arm):** per 30-second epoch and per region (frontal, central, posterior, temporal): log and relative power in delta, theta, alpha, sigma and beta, 95% spectral edge, theta/alpha ratio, Hjorth mobility and complexity; slow and fast eye-channel power. 67 features, plus a ±2-epoch context average. The ECG channel is never used as a feature.
5. **Model and testing:** gradient-boosted trees with balanced class weights; **leave-one-person-out** cross-validation, so each person is scored by a model that never saw them. Features are robust-scaled within each person.
6. **Statistics:** Cohen's kappa against the expert for each person; arms compared with paired Wilcoxon signed-rank tests and bootstrap 95% confidence intervals of the mean difference. A stratified-chance classifier gives the floor.

## Results so far

Effect of cleaning on participant 1 (sleep run 1, 15 minutes; [`cleaning_effect.py`](cleaning_effect.py)):

| Measure | Uncleaned | Cleaned |
|---|---|---|
| Heartbeat artefact, O1, average of 1,229 beats | 86 µV peak-to-peak | 4 µV |
| Sleep-spindle band (sigma, 12–16 Hz) power, scalp mean | 23.5 µV²/Hz | 7.2 µV²/Hz (3.3× lower) |
| Beta band (16–30 Hz) power, scalp mean | 81.6 µV²/Hz | 1.3 µV²/Hz (62× lower) |

![Power spectrum before and after cleaning](../../figures/sub-01_task-sleep_run-1_psd.png)

Classifier comparison across all 33 people: **running**.

## What does cleaning remove?

Measured on participant 1, sleep run 1, with [`data_accounting.py`](data_accounting.py):

| Step | What is removed | Share | Importance for sleep staging |
|---|---|---|---|
| Crop to scanning period | Seconds before the first and after the last scanner volume | 3.5% of recording time | None: these seconds have no sleep labels |
| Gradient subtraction | Scanner artefact | 99.68% of raw signal power | None: artefact; brain loss is about 1/21 (4.8%) of brain power, about 0.015% of raw power |
| 0.3–40 Hz filter | Slow drift below 0.3 Hz (10.5%) and activity above 40 Hz (2.3%) | 12.8% of remaining power | Low: sleep scoring uses 0.3–35 Hz; very slow brain activity and gamma are lost |
| Resample to 250 Hz | Samples that only describe frequencies above 125 Hz | 95% of samples | None after the 40 Hz filter |
| Heartbeat subtraction | Pulse artefact | 19.9% of filtered power: delta 22%, theta 31%, alpha 38%, sigma 57%, beta 34% | Mostly artefact (see below); about 4.8% of brain power goes with the template |
| Label tidying | Uncertain or unscorable epochs; N3 merged into N2 | 1.9% of epochs dropped; 0.6% relabelled | Deep sleep can't be studied as its own stage |

**Is the large sigma-band removal real artefact?** Heartbeat removal with MNE's standard R-peak detector keeps more sigma-band power (14.4 vs 7.1 µV²/Hz), but its beat times scatter by up to 28 ms, and checked against precise beat times it leaves 42 µV of heartbeat artefact versus 5.5 µV for ours. The extra power is residual artefact, not preserved brain signal.

## Is brain signal preserved?

[`signal_preservation.py`](signal_preservation.py) compares the cleaned scanning period with the 24 seconds recorded before the first scanner volume. Between 0.5 and 15 Hz both have the same shape, including the alpha peak near 10 Hz and a spindle-range peak near 13 Hz, so cleaning keeps the brain rhythms sleep staging relies on.

![Pre-scan vs cleaned scanning spectrum](results/signal_preservation_sub-01.png)

The check also showed:

- The pre-scan stretch already contains the 16.7 Hz slice rhythm, so the scanner was running unmarked warm-up volumes. It is a useful but imperfect reference.
- The 38.5 Hz peak is present before scanning too: it comes from other scanner-room equipment, not from incomplete gradient removal, and needs a targeted notch filter.
- Peaks at about 3 and 6 Hz appear only during scanning and may be residual artefact; to investigate.
- The percentile-based R-peak detector under-detects on short stretches (7 of 32 beats in 24 s), though on full recordings it is more precise than MNE's (see above). This comparison used MNE's detector, which leaves residual heartbeat artefact, so its sigma and beta bands are inflated on both sides. To be redone with a detector that is both robust and precise.

## Limitations

- Narrow residual artefact peaks between 20 and 48 Hz remain after cleaning (visible in the spectrum above).
- The artefact templates include the current volume or heartbeat, which subtracts about 1/21 (5%) of that segment's own brain signal; excluding it is a planned refinement.
- Cleaning removes any brain response genuinely locked to the heartbeat (heartbeat-evoked potentials, a few µV). This doesn't affect sleep staging but would matter for research on body–brain signals.
- Naps in a scanner contain almost no deep sleep, and only 16 of 33 people have 10 or more minutes of N2.
- 33 people is a small sample; results are reported per person with confidence intervals, not only as one pooled number.

## Reproduce

```bash
python studies/01-preprocessing-ablation/build_dataset.py     # download, clean, extract features (~5 h; ~0.5 GB disk at a time)
python studies/01-preprocessing-ablation/compare_arms.py      # leave-one-person-out comparison -> results/
python studies/01-preprocessing-ablation/cleaning_effect.py <recording.vhdr>
```
