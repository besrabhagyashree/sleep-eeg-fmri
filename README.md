# Sleep EEG-fMRI

**Bhagyashree Besra** · started October 2026 · work in progress

Research on sleep and wakefulness using EEG recorded simultaneously with fMRI. The project is built in stages, each a reusable part of the pipeline, and answers its research questions as separate studies that share that pipeline.

## Pipeline stages

| Stage | Folder | What it does | Status |
|---|---|---|---|
| **1. Preprocessing** | [`src/preprocessing`](src/preprocessing) | Removes MRI scanner and heartbeat artefacts, filters and resamples the EEG | Scanner + heartbeat removal done; residual peaks, bad channels, re-referencing, movement to do |
| **2. Features** | [`src/features`](src/features) | Turns each 30-second epoch into numbers: band power, spectral shape, eye movements | Spectral features done; spindle detection to do |
| **3. Research methods** | [`src/methods`](src/methods) | The analyses that answer each question: sleep-stage classification, alpha-rhythm analysis | In progress |
| **4. Post-processing** | [`src/postprocessing`](src/postprocessing) | Statistics, figures and reports | Example figures done |

## Studies

| # | Question | Status |
|---|---|---|
| [01](studies/01-preprocessing-ablation) | **Does preprocessing matter?** The same sleep-staging classifier on raw, filtered-only and fully cleaned EEG | Running on all 33 people |
| 02 | **Alpha before and after learning:** does individual alpha frequency change after a visual-motor task? | Planned |

## Data

[OpenNeuro ds003768](https://openneuro.org/datasets/ds003768/versions/1.0.13): simultaneous EEG and fMRI from 33 healthy adults resting and napping in a 3T scanner, with expert sleep-stage labels for every 30 seconds (Gu et al., Penn State; CC0 licence). The data is not stored in this repository; the scripts download it from OpenNeuro.

![Raw, gradient-corrected and fully cleaned EEG](figures/sub-01_task-sleep_run-1_stages.png)

*Stage 1 on participant 1: raw in-scanner EEG (top), after scanner-artefact removal (middle) and after heartbeat removal (bottom).*

## Repository layout

```
src/            reusable pipeline code, one folder per stage
studies/        one folder per research question: its scripts, results and write-up
figures/        figures shared across studies
```

## Reproduce

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows; .venv/bin on Linux/macOS
python src/preprocessing/mr_artifacts.py <recording.vhdr>              # clean one recording, with figures
python src/postprocessing/example_figures.py                           # example figures for participant 1
```

Each study's README gives the commands for that study.

## Citation

Gu, Y., Han, F., Sainburg, L. E., Schade, M. M., Buxton, O. M., Duyn, J. H., & Liu, X. (2021). *An orderly sequence of autonomic and neural events at transient arousal changes.* bioRxiv. Dataset: OpenNeuro ds003768, doi:10.18112/openneuro.ds003768.v1.0.0.
