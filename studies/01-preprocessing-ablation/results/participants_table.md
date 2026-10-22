<img alt="progress" src="https://img.shields.io/badge/participants%20built-8%20of%2033-d97706?style=for-the-badge"> <img alt="percent" src="https://img.shields.io/badge/progress-24%25-33318a?style=for-the-badge">

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
| 06 | ⬛ -0.10 | 🟥 0.10 | 🟥 0.18 | 🟥 0.09 | ⬛ -0.12 | ⬛ -0.11 | ⬛ -0.11 | ⬛ -0.11 |
| 07 | 🟥 0.16 | 🟥 0.09 | 🟥 0.10 | 🟥 0.09 | ⬛ -0.04 | ⬛ -0.03 | ⬛ -0.04 | ⬛ -0.03 |
| 08 | ⬛ -0.01 | ⬛ -0.01 | ⬛ -0.01 | ⬛ -0.01 | – | – | – | – |
| **median** | **⬛ -0.01** | **🟥 0.09** | **⬛ -0.01** | **⬛ -0.01** | **⬛ -0.04** | **⬛ -0.03** | **⬛ -0.01** | **⬛ -0.03** |

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
