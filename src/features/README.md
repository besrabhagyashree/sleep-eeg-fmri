# Stage 2: Features

| Set | Code | Features per 30-second epoch | Method | Used in |
|---|---|---|---|---|
| Spectral (primary) | `spectral.py` | Band power (delta, theta, alpha, sigma, beta), relative power, spectral edge, theta/alpha ratio and Hjorth parameters per scalp region; eye-channel power | Welch (1967); Hjorth (1970) | Main analysis, all arms |
| Sleep events (secondary) | `events.py` | Spindle density, amplitude, frequency, duration (C3–M2, C4–M1) | YASA `spindles_detect` (Vallat & Walker, 2021; Lacourse et al., 2019) | Amendment 6, registered arms |
| | | Slow-wave density, peak-to-peak amplitude, slope (F3–M2, F4–M1) | YASA `sw_detect` (Massimini et al., 2004; Carrier et al., 2011) | |
| | | Alpha peak frequency and power (O1–M2, O2–M1) | Klimesch (1999) | |

Both work at any sampling rate, so raw 5 kHz data and cleaned 250 Hz data go through the same code.

Event detection runs on the whole continuous recording, never sees the expert's stages, and uses the AASM mastoid derivations: the recording reference (FCz) sits between Fz and Cz and cancels much of their activity. Not included: K-complexes, which have no detector of comparable standing in open software.
