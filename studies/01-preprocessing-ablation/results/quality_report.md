| Check | Result |
|---|---|
| Files: size + MD5 match OpenNeuro, 32 channels, ECG/EOG, regular triggers | 252 of 255 recordings pass |
| Files agree with the dataset's metadata (sampling rate) | 1 of 255 (metadata says 250.0 Hz; files are 5000 Hz) |
| Channels: <= 3 bad channels (PREP) | 251 of 255 recordings pass |
| Epochs: <= 25% flagged by Autoreject | 29 of 33 people pass; 1111 of 6780 epochs flagged (16.4%) |
| Epochs the dataset's expert marked uncertain/unscorable | 131 (excluded) |

| Measurement (median over recordings) | MNE detector | Refined detector |
|---|---|---|
| Heartbeat removal, INPS (dB, higher = more removed) | 1.35 | 1.62 |
| Double-counted beats per recording | 58 | 0 |
| Missed-beat gaps per recording | 15 | 1 |

Residual scanner peak after cleaning: 3.0 dB at the slice frequency, 9.3 dB at its 2nd harmonic (above the neighbouring spectrum; median).
