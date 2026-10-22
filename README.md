<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img alt="Sleep EEG-fMRI: raw in-scanner EEG and the same EEG after cleaning" src="assets/banner-light.svg" width="100%">
</picture>

<p align="center">
  <a href="https://github.com/besrabhagyashree/sleep-eeg-fmri/actions/workflows/tests.yml"><img alt="Tests" src="https://img.shields.io/github/actions/workflow/status/besrabhagyashree/sleep-eeg-fmri/tests.yml?branch=main&label=tests&style=for-the-badge&logo=github"></a>
  <img alt="Status: work in progress" src="https://img.shields.io/badge/status-work%20in%20progress-f59e0b?style=for-the-badge">
  <img alt="Python 3.11" src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="MNE-Python 1.13" src="https://img.shields.io/badge/MNE--Python-1.13-0b7285?style=for-the-badge">
  <img alt="scikit-learn" src="https://img.shields.io/badge/scikit--learn-1.9-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white">
  <img alt="Data: OpenNeuro ds003768" src="https://img.shields.io/badge/data-OpenNeuro%20ds003768-33318a?style=for-the-badge">
  <img alt="33 participants" src="https://img.shields.io/badge/participants-33-b53b6d?style=for-the-badge">
  <a href="https://orcid.org/0009-0008-6118-7602"><img alt="ORCID 0009-0008-6118-7602" src="https://img.shields.io/badge/ORCID-0009--0008--6118--7602-A6CE39?style=for-the-badge&logo=orcid&logoColor=white"></a>
  <a href="LICENSE"><img alt="MIT licence" src="https://img.shields.io/badge/licence-MIT-0f766e?style=for-the-badge"></a>
</p>

Research on sleep and wakefulness using **EEG recorded simultaneously with fMRI**. Inside a working MRI scanner, the EEG is buried under artefacts hundreds of times larger than brain activity (top trace above). This project builds a pipeline that cleans it, measures it and models it, then uses that pipeline to answer research questions as separate studies.

**Author:** Bhagyashree Besra · [ORCID 0009-0008-6118-7602](https://orcid.org/0009-0008-6118-7602) · [portfolio](https://besrabhagyashree.github.io) · started October 2026

## ✨ At a glance

| | Uncleaned | Cleaned |
|---|:---:|:---:|
| 💓 Heartbeat artefact (O1, average of 1,229 beats) | 86 µV | **4 µV** |
| 🌙 Sleep-spindle band power (12–16 Hz) | 23.5 µV²/Hz | **7.1 µV²/Hz** · 3.3× lower |
| 📡 Beta band power, mostly scanner noise (16–30 Hz) | 81.6 µV²/Hz | **1.3 µV²/Hz** · 62× lower |

<sub>Participant 1, 15-minute sleep recording, mean of 30 scalp channels.</sub>

## 🧭 Pipeline

```mermaid
flowchart TB
    RAW["🧠 Raw EEG<br/>32 channels · 5 kHz"]:::data

    subgraph S1 ["1 · Preprocessing"]
        direction LR
        P1["1 · Scanner<br/>artefact"]:::done --> P2["2 · Heartbeat<br/>artefact"]:::done --> P3["3 · Filter<br/>250 Hz"]:::done --> P4A["4a · OBS<br/>tested, not used"]:::rejected --> P4B["4b · Notch<br/>33.3 / 38.5 Hz"]:::done --> P5["5 · Bad<br/>channels"]:::done --> P6["6 · Re-<br/>reference"]:::wip --> P7["7 · Movement<br/>Autoreject"]:::done
    end
    subgraph S2 ["2 · Features"]
        direction LR
        F1["Band power · spectra"]:::done ~~~ F2["Spindles · alpha peak"]:::todo
    end
    subgraph S3 ["3 · Research methods"]
        direction LR
        M1["Sleep-stage classifier"]:::wip ~~~ M2["Alpha analysis"]:::todo
    end
    LAB["📋 Expert sleep labels<br/>every 30 seconds"]:::data
    subgraph S4 ["4 · Post-processing"]
        direction LR
        Q1["Figures"]:::done ~~~ Q2["Statistics"]:::wip
    end

    RAW --> S1 --> S2 --> S3 --> S4
    LAB --> S3

    classDef done fill:#d1fae5,stroke:#059669,color:#064e3b
    classDef wip fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef todo fill:#f1f5f9,stroke:#94a3b8,color:#334155,stroke-dasharray: 4 3
    classDef data fill:#ede9fe,stroke:#6d28d9,color:#2e1065
    classDef rejected fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-dasharray: 2 2
    style S1 fill:#f8fafc,stroke:#cbd5e1,color:#0f172a
    style S2 fill:#f8fafc,stroke:#cbd5e1,color:#0f172a
    style S3 fill:#f8fafc,stroke:#cbd5e1,color:#0f172a
    style S4 fill:#f8fafc,stroke:#cbd5e1,color:#0f172a
```

<p align="center">
  <img alt="done" src="https://img.shields.io/badge/●-done-059669?style=flat-square">
  <img alt="in progress" src="https://img.shields.io/badge/●-in%20progress-d97706?style=flat-square">
  <img alt="planned" src="https://img.shields.io/badge/●-planned-94a3b8?style=flat-square">
  <img alt="tested, not adopted" src="https://img.shields.io/badge/●-tested%2C%20not%20adopted-dc2626?style=flat-square">
</p>

| Stage | Folder | What it does | Status |
|---|---|---|---|
| 🧹 **1. Preprocessing** | [`src/preprocessing`](src/preprocessing) | Scanner and heartbeat artefact removal, filtering, notch, bad-channel repair, re-reference, movement exclusion; quality checks at every level | ![](https://img.shields.io/badge/7%20of%207%20steps-addressed-059669?style=flat-square) ![](https://img.shields.io/badge/reference-chosen%20at%2033%20people-d97706?style=flat-square) |
| 📊 **2. Features** | [`src/features`](src/features) | Turns each 30-second epoch into band power, spectral shape and eye-movement numbers | ![](https://img.shields.io/badge/spectral-done-059669?style=flat-square) ![](https://img.shields.io/badge/spindles-planned-94a3b8?style=flat-square) |
| 🔬 **3. Research methods** | [`src/methods`](src/methods) | The analyses that answer each question: sleep-stage classification, alpha rhythms | ![](https://img.shields.io/badge/classifier-in%20progress-d97706?style=flat-square) |
| 📈 **4. Post-processing** | [`src/postprocessing`](src/postprocessing) | Statistics, figures and reports | ![](https://img.shields.io/badge/figures-done-059669?style=flat-square) ![](https://img.shields.io/badge/statistics-in%20progress-d97706?style=flat-square) |

## 🔬 Studies

| # | Question | Status |
|:---:|---|---|
| [**01**](studies/01-preprocessing-ablation) | **Does preprocessing matter?** The same sleep-staging classifier on raw, filtered-only and fully cleaned EEG, tested on people it never saw | ![](https://img.shields.io/badge/running-33%20people-d97706?style=flat-square) |
| **02** | **Alpha before and after learning:** does a person's alpha-rhythm frequency change after a visual-motor task? | ![](https://img.shields.io/badge/-planned-94a3b8?style=flat-square) |

> [!IMPORTANT]
> Study 01's classifier results across all 33 people are being computed now and will be added here when complete, whatever they show.

## 🗂️ Data

[OpenNeuro ds003768](https://openneuro.org/datasets/ds003768/versions/1.0.13): simultaneous EEG and fMRI from 33 healthy adults resting and napping in a 3T scanner, with expert sleep-stage labels for every 30 seconds (Gu et al., 2022, *NeuroImage*; Penn State; CC0 licence).

| Wake | N1 (drowsy) | N2 (light sleep) | N3 (deep sleep) |
|:---:|:---:|:---:|:---:|
| 3,343 epochs | 2,148 epochs | 1,325 epochs | 42 epochs |

> [!NOTE]
> No data is stored in this repository. The scripts download it directly from OpenNeuro, one recording at a time.

<p align="center">
  <img alt="Raw, gradient-corrected and fully cleaned EEG" src="figures/sub-01_task-sleep_run-1_stages.png" width="88%">
  <br><sub>Stage 1 on participant 1: raw in-scanner EEG (top), after scanner-artefact removal (middle), after heartbeat removal (bottom).</sub>
</p>

<details>
<summary><b>📁 Repository layout</b></summary>

```
src/
├── preprocessing/    stage 1: artefact removal, filtering
├── features/         stage 2: per-epoch features
├── methods/          stage 3: research methods
└── postprocessing/   stage 4: statistics, figures, this README's banner
studies/
└── 01-preprocessing-ablation/   question, scripts, results
figures/              figures shared across studies
assets/               README banner (drawn from real data by src/postprocessing/readme_banner.py)
```
</details>

<details>
<summary><b>▶️ Reproduce</b></summary>

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows; .venv/bin on Linux/macOS
python src/preprocessing/mr_artifacts.py <recording.vhdr>              # clean one recording, with figures
python src/postprocessing/example_figures.py                           # example figures for participant 1
```

Each study's README gives the commands for that study.
</details>

## 📚 Citation

Gu, Y., Han, F., Sainburg, L. E., Schade, M. M., Buxton, O. M., Duyn, J. H., & Liu, X. (2022). An orderly sequence of autonomic and neural events at transient arousal changes. *NeuroImage*, 264, 119720. [doi:10.1016/j.neuroimage.2022.119720](https://doi.org/10.1016/j.neuroimage.2022.119720). Dataset: OpenNeuro ds003768, [doi:10.18112/openneuro.ds003768.v1.0.0](https://doi.org/10.18112/openneuro.ds003768.v1.0.0).

**Every method, metric, standard and software package used in this project is cited in full, with DOIs, in [REFERENCES.md](REFERENCES.md).**
