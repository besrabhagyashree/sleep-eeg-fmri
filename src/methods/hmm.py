"""Hidden Markov model decoding of per-epoch class probabilities (Rabiner, 1989).

Used in study 01b (method C): transitions and initial probabilities come from training participants' expert
hypnograms; a classifier's posterior divided by the training class prior serves as the emission score;
the Viterbi algorithm returns the most probable stage sequence for a recording.
"""
import numpy as np


def transitions(sequences, classes, smoothing=1.0):
    """Row-stochastic transition matrix and initial probabilities from lists of stage labels."""
    k = {c: i for i, c in enumerate(classes)}
    T = np.full((len(classes), len(classes)), smoothing)
    init = np.full(len(classes), smoothing)
    for seq in sequences:
        if len(seq) == 0:
            continue
        init[k[seq[0]]] += 1
        for a, b in zip(seq, seq[1:]):
            T[k[a], k[b]] += 1
    return T / T.sum(1, keepdims=True), init / init.sum()


def viterbi(posteriors, priors, T, init):
    """Most probable state path. posteriors: (n_epochs, n_classes) classifier probabilities."""
    logT, logI = np.log(T), np.log(init)
    emit = np.log(np.clip(posteriors, 1e-12, None)) - np.log(np.clip(priors, 1e-12, None))
    n, k = emit.shape
    score, back = logI + emit[0], np.zeros((n, k), dtype=int)
    for i in range(1, n):
        cand = score[:, None] + logT                    # previous state x next state
        back[i] = cand.argmax(0)
        score = cand.max(0) + emit[i]
    path = [int(score.argmax())]
    for i in range(n - 1, 0, -1):
        path.append(int(back[i, path[-1]]))
    return np.array(path[::-1])
