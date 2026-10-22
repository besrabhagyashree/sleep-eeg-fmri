# Does preprocessing matter? Sleep staging from EEG recorded inside an MRI scanner

**Bhagyashree Besra** · started October 2026 · work in progress

EEG recorded during fMRI is buried under scanner and heartbeat artefacts hundreds of times larger than brain activity. Labs routinely remove them before analysis, but how much does that cleaning actually change what a sleep-staging model can learn?

This project answers that with an **ablation study**: the same sleep-staging classifier, trained and tested on the same people and the same expert labels, using three versions of the same EEG:

| Arm | EEG used |
|---|---|
| **raw** | Straight from the dataset: 5 kHz, nothing removed or filtered |
| **filtered** | 0.3–40 Hz filter, 250 Hz, no artefact removal |
| **cleaned** | Scanner (gradient) and heartbeat (ballistocardiogram) artefacts removed, then the same filter |

## Data

[OpenNeuro ds003768](https://openneuro.org/datasets/ds003768/versions/1.0.13): simultaneous EEG and fMRI from 33 healthy adults resting and napping in a 3T scanner, with expert sleep-stage labels for every 30 seconds (Gu et al., Penn State; CC0 licence). Analysed here: 32-channel EEG and the stage labels, 6,858 cleanly labelled epochs (wake 3,343, N1 2,148, N2 1,325, N3 42). N3 is too rare to model and is merged with N2.

The data is not included in this repository; the scripts download it directly from OpenNeuro.

## Methods

1. **Scanner artefact:** average artefact subtraction locked to the R128 volume triggers, 21-volume sliding template (Allen, Josephs & Turner, 2000, *NeuroImage*).
2. **Heartbeat artefact:** R-peaks detected in the ECG channel, then average artefact subtraction locked to each beat, 21-beat template (Allen et al., 1998, *NeuroImage*).
3. **Filter and resample:** 0.3–40 Hz, 250 Hz.
4. **Features (identical for every arm):** per 30-second epoch and per region (frontal, central, posterior, temporal): log and relative power in delta, theta, alpha, sigma and beta bands, 95% spectral edge, theta/alpha ratio, Hjorth mobility and complexity; slow and fast eye-channel power. 67 features, plus a ±2-epoch context average.
5. **Model and testing:** gradient-boosted trees with balanced class weights, **leave-one-person-out** cross-validation (each person is scored by a model that never saw them), features robust-scaled within each person.
6. **Statistics:** Cohen's kappa against the expert per person; arms compared with paired Wilcoxon signed-rank tests and bootstrap 95% confidence intervals.

## Results so far

Cleaning on participant 1 (sleep run 1, 15 minutes):

| What | Before | After |
|---|---|---|
| Heartbeat artefact, O1, average over 1,229 beats | 86 µV peak-to-peak | 4 µV |
| Sleep-spindle band (sigma, 12–16 Hz) power, scalp mean | 23.5 µV²/Hz | 7.2 µV²/Hz (3.3× lower) |
| Beta band (16–30 Hz) power, scalp mean | 81.6 µV²/Hz | 1.3 µV²/Hz (62× lower) |

![Raw, gradient-corrected and fully cleaned EEG](figures/sub-01_task-sleep_run-1_stages.png)

![Power spectrum before and after cleaning](figures/sub-01_task-sleep_run-1_psd.png)

Classifier comparison across all 33 people: **running**.

## Status

- [x] Scanner and heartbeat artefact removal
- [x] Feature extraction for all three arms
- [ ] Full 33-person feature build (in progress)
- [ ] Classifier comparison and statistics
- [ ] Remaining cleaning: residual 20–48 Hz peaks (optimal basis sets), bad channels, mastoid re-reference, movement bursts
- [ ] Individual alpha frequency before vs after a visual-motor learning task

## Known limitations

- Narrow residual artefact peaks between 20 and 48 Hz remain after cleaning (visible in the spectrum above).
- Naps in a scanner contain almost no deep sleep (N3), and only 16 of 33 people have 10 or more minutes of N2.
- 33 people is a small sample; results are reported per person with confidence intervals, not only as one pooled number.

## Reproduce

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows; use .venv/bin on Linux/macOS
python src/build_dataset.py            # downloads, cleans and extracts features (~5 h; ~0.5 GB disk at a time)
python src/train_eval.py               # leave-one-person-out comparison -> results/
python src/mr_artifacts.py <run.vhdr>  # cleaning figures for one recording
```

## Citation

Gu, Y., Han, F., Sainburg, L. E., Schade, M. M., Buxton, O. M., Duyn, J. H., & Liu, X. (2021). *An orderly sequence of autonomic and neural events at transient arousal changes.* bioRxiv. Dataset: OpenNeuro ds003768, doi:10.18112/openneuro.ds003768.v1.0.0.
