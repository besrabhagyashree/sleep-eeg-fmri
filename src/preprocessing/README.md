# Stage 1: Preprocessing

Makes in-scanner EEG usable. All seven steps are addressed:

| # | Step | Method | Code | Used in |
|---|---|---|---|---|
| 1 | Scanner (gradient) artefact | Average artefact subtraction (Allen et al., 2000) | `mr_artifacts.py` | All cleaned versions |
| 2 | Heartbeat artefact | Average artefact subtraction (Allen et al., 1998); MNE detector or refined timing | `mr_artifacts.py` | All cleaned versions |
| 3 | Filter and resample | 0.3–40 Hz FIR, 250 Hz | build scripts | Filtered and cleaned versions |
| 4a | Residual heartbeat artefact | Optimal basis sets (Niazy et al., 2005) | `mr_artifacts.remove_bcg_obs` | **Tested, not adopted**: removes ~75% of slow-wave (delta) power even where there is no heartbeat |
| 4b | Residual narrow-band peaks | FIR notch at 33.3 Hz (slice harmonic) and 38.5 Hz (scanner-room equipment) | `stages.py` | Fully-cleaned version |
| 5 | Bad channels | PREP detection, spherical-spline interpolation (Perrin et al., 1989) | `quality.py`, `stages.py` | Fully-cleaned version |
| 6 | Re-reference | Linked mastoids or average reference, chosen by a pre-registered rule | `stages.py` | Fully-cleaned version |
| 7 | Movement | Autoreject epoch rejection (Jas et al., 2017) | `quality.py` | All versions (identical exclusions) |

- `quality.py`: data-quality checks at four levels: file checksums and header; PREP bad channels; Autoreject epoch thresholds; correction quality (INPS, residual scanner peaks, heartbeat detection).
