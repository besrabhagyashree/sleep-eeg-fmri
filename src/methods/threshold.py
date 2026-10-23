"""Decision threshold for one class chosen by Youden's J (Youden, 1950), and the matching decision rule.

Used in study 01b amendment 1: the threshold is chosen on out-of-fold probabilities of training participants
only, then applied unchanged to a held-out participant.
"""
import numpy as np

GRID = np.round(np.arange(0.05, 0.951, 0.01), 2)


def youden_threshold(is_target, prob, grid=GRID):
    """Threshold maximising sensitivity + specificity - 1 for 'prob >= threshold' predicting the target class."""
    is_target = np.asarray(is_target, bool)
    prob = np.asarray(prob, float)
    best_t, best_j = 0.5, -np.inf
    for t in grid:
        pred = prob >= t
        sens = (pred & is_target).sum() / max(is_target.sum(), 1)
        spec = (~pred & ~is_target).sum() / max((~is_target).sum(), 1)
        if sens + spec - 1 > best_j:                            # ties keep the lower threshold
            best_t, best_j = float(t), sens + spec - 1
    return best_t, best_j


def decide(P, classes, target, threshold):
    """Target class if its probability >= threshold, else the most probable of the other classes."""
    P = np.asarray(P, float)
    k = classes.index(target)
    others = [i for i in range(len(classes)) if i != k]
    rest = np.array(classes, dtype=object)[np.array(others)[P[:, others].argmax(1)]]
    return np.where(P[:, k] >= threshold, target, rest)
