"""The amendment-1 reference-selection rule, on scores with a known answer."""
import pandas as pd

from build_full_stages import choose_reference


def _scores(mastoid, average):
    rows = [{"subject": f"{i:02d}", "reference": "full_mastoid", "score": m} for i, m in enumerate(mastoid)]
    rows += [{"subject": f"{i:02d}", "reference": "full_average", "score": a} for i, a in enumerate(average)]
    return pd.DataFrame(rows)


def test_higher_median_wins():
    assert choose_reference(_scores([0.9, 1.0, 1.1], [0.5, 0.6, 0.7]))[0] == "full_mastoid"
    assert choose_reference(_scores([0.5, 0.6, 0.7], [0.9, 1.0, 1.1]))[0] == "full_average"


def test_ties_go_to_the_average_reference():
    assert choose_reference(_scores([0.705, 0.705], [0.70, 0.70]))[0] == "full_average"   # difference 0.005 < 0.01


def test_unscorable_participants_are_ignored():
    s = _scores([2.0, None, None], [1.0, None, None])
    choice, med = choose_reference(s)
    assert choice == "full_mastoid" and med["full_mastoid"] == 2.0
