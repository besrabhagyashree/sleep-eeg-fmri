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


def corner_threshold(is_target, prob, grid=GRID):
    """Threshold whose ROC point is closest to the top-left corner (sensitivity 1, specificity 1)."""
    is_target = np.asarray(is_target, bool)
    prob = np.asarray(prob, float)
    best_t, best_d = 0.5, np.inf
    for t in grid:
        pred = prob >= t
        sens = (pred & is_target).sum() / max(is_target.sum(), 1)
        spec = (~pred & ~is_target).sum() / max((~is_target).sum(), 1)
        dist = np.hypot(1 - sens, 1 - spec)
        if dist < best_d:
            best_t, best_d = float(t), dist
    return best_t, best_d


def f1_threshold(P, y, classes, target, grid=GRID):
    """Threshold maximising the target class's F1 under decide() on the given (training, out-of-fold) data."""
    y = np.asarray(y, dtype=object)
    best_t, best_f = 0.5, -1.0
    for t in grid:
        pred = decide(P, classes, target, t)
        tp = np.sum((pred == target) & (y == target))
        fp, fn = np.sum((pred == target) & (y != target)), np.sum((pred != target) & (y == target))
        f = 2 * tp / max(2 * tp + fp + fn, 1)
        if f > best_f:
            best_t, best_f = float(t), f
    return best_t, best_f
