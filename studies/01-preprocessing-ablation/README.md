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
> The main result (each person scored by a model trained on everyone else, with significance tests across people) appears in the tables below once all 33 participants are built. Until then, only data quality and within-person previews are shown.

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
<img alt="progress" src="https://img.shields.io/badge/participants%20built-5%20of%2033-d97706?style=for-the-badge"> <img alt="percent" src="https://img.shields.io/badge/progress-15%25-33318a?style=for-the-badge">

**Kappa colours** follow the Landis & Koch (1977) agreement bands: ⬛ ≤ 0 none · 🟥 0.01–0.20 slight · 🟧 0.21–0.40 fair · 🟨 0.41–0.60 moderate · 🟩 0.61–0.80 substantial · 💚 0.81–1.00 almost perfect

<details open>
<summary><b>🎯 Main result: scored by a model trained on all other people</b></summary>

> [!NOTE]
> Available when all 33 participants are built.

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
| **median** | **🟥 0.14** | **🟥 0.12** | **⬛ -0.01** | **⬛ -0.03** | **⬛ -0.03** | **🟥 0.03** | **🟧 0.21** | **🟥 0.18** |

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
| 06 | ⏳ processing | | | | | | | |
| 07 | ⏳ processing | | | | | | | |
| 08 | ⏳ processing | | | | | | | |
| 09 | ⏳ processing | | | | | | | |
| 10 | ⏳ processing | | | | | | | |
| 11 | ⏳ processing | | | | | | | |
| 12 | ⏳ processing | | | | | | | |
| 13 | ⏳ processing | | | | | | | |
| 14 | ⏳ processing | | | | | | | |
| 15 | ⏳ processing | | | | | | | |
| 16 | ⏳ processing | | | | | | | |
| 17 | ⏳ processing | | | | | | | |
| 18 | ⏳ processing | | | | | | | |
| 19 | ⏳ processing | | | | | | | |
| 20 | ⏳ processing | | | | | | | |
| 21 | ⏳ processing | | | | | | | |
| 22 | ⏳ processing | | | | | | | |
| 23 | ⏳ processing | | | | | | | |
| 24 | ⏳ processing | | | | | | | |
| 25 | ⏳ processing | | | | | | | |
| 26 | ⏳ processing | | | | | | | |
| 27 | ⏳ processing | | | | | | | |
| 28 | ⏳ processing | | | | | | | |
| 29 | ⏳ processing | | | | | | | |
| 30 | ⏳ processing | | | | | | | |
| 31 | ⏳ processing | | | | | | | |
| 32 | ⏳ processing | | | | | | | |
| 33 | ⏳ processing | | | | | | | |

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
</details>

> [!TIP]
> The analysis plan, exclusions and tests are fixed in [PREREGISTRATION.md](PREREGISTRATION.md), written before the full results.

## 📚 References

Full citations with DOIs for every method, metric, dataset and software package: **[REFERENCES.md](../../REFERENCES.md)**. Planned next cleaning step: optimal basis sets (Niazy et al., 2005).

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
