"""Evaluation: no leakage between people, and correct paired statistics."""
import numpy as np
import pandas as pd

from compare_arms import evaluate, paired


def _people(n_people=8, n_epochs=40, seed=0):
    """Each person has their own arbitrary feature-to-stage mapping, so nothing generalises across people."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_people):
        flip = rng.choice([-1, 1], size=4)
        for i in range(n_epochs):
            stage = ["W", "N1", "N2"][i % 3]
            base = {"W": 1.0, "N1": 0.0, "N2": -1.0}[stage]
            f = {f"f{k}": flip[k] * base + rng.normal(0, 0.3) for k in range(4)}
            rows.append({"subject": f"{s:02d}", "session": "r1", "t": 30.0 * i, "stage": stage, "arm": "x", **f})
    return pd.DataFrame(rows)


def test_leave_one_person_out_does_not_leak():
    """Within-person the stages are perfectly separable; across people they are not.
    A leaky evaluation would score high here. Leave-one-person-out must stay near chance."""
    d = _people()
    _, pooled, _ = evaluate(d, ["f0", "f1", "f2", "f3"], ["W", "N1", "N2"], "logreg", norm=False, context=False)
    assert pooled["kappa"] < 0.5


def test_paired_difference_and_confidence_interval():
    a = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
    b = a + 0.1
    r = paired(a, b)
    assert r["mean_diff"] == pytest_approx(0.1) and r["median_diff"] == pytest_approx(0.1)
    assert r["people_improved"] == 7 and r["people_worse"] == 0
    assert r["ci95"][0] <= 0.1 <= r["ci95"][1]


def pytest_approx(v):
    import pytest
    return pytest.approx(v)
