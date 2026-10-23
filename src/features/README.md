# Stage 2: Features

| Set | Code | Features per 30-second epoch | Method | Used in |
|---|---|---|---|---|
| Spectral (primary) | `spectral.py` | Band power (delta, theta, alpha, sigma, beta), relative power, spectral edge, theta/alpha ratio and Hjorth parameters per scalp region; eye-channel power | Welch (1967); Hjorth (1970) | Main analysis, all arms |
| Sleep events (secondary) | `events.py` | Spindle density, amplitude, frequency, duration (C4–M1; backup C3–M2) | YASA `spindles_detect` (Vallat & Walker, 2021; Lacourse et al., 2019) | Amendment 6, registered arms |
| | | Slow-wave density, peak-to-peak amplitude, slope (F4–M1; backup F3–M2) | YASA `sw_detect` (Massimini et al., 2004; Carrier et al., 2011) | |
| | | Alpha peak frequency and power (O2–M1; backup O1–M2) | Klimesch (1999) | |

Both work at any sampling rate, so raw 5 kHz data and cleaned 250 Hz data go through the same code.

Event detection runs on the whole continuous recording, never sees the expert's stages, and uses the AASM recommended derivations, switching to the backup only when PREP marks an electrode bad: the recording reference (FCz) sits between Fz and Cz and cancels much of their activity. Not included: K-complexes, which have no detector of comparable standing in open software.

Band edges: spectral bands are half-open (lo ≤ f < hi, e.g. alpha 8–12 Hz leaves out the 12 Hz bin); the alpha-peak search range is closed (7 ≤ f ≤ 13 Hz). Both use 4-s Welch windows (0.25 Hz bins).
