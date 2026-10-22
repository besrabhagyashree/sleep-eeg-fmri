# Stage 1: Preprocessing

Makes in-scanner EEG usable.

- `mr_artifacts.py`: removes the MRI gradient artefact and the heartbeat (ballistocardiogram) artefact by average artefact subtraction, filters to 0.3–40 Hz and resamples to 250 Hz. Run on one recording to get cleaned data plus before/after figures.

Planned: residual-artefact removal with optimal basis sets, bad-channel detection and repair, mastoid re-referencing, movement-burst marking.
