"""Shared test setup: import paths and helpers for synthetic signals with known answers."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
STUDY = ROOT / "studies" / "01-preprocessing-ablation"
sys.path.insert(0, str(STUDY))


def load_study_module(name):
    spec = importlib.util.spec_from_file_location(name, STUDY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def rng():
    return np.random.default_rng(0)


@pytest.fixture
def ch_names():
    return ["Fp1", "Fp2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "F7", "F8", "T7", "T8", "P7", "P8",
            "Fz", "Cz", "Pz", "Oz", "FC1", "FC2", "CP1", "CP2", "FC5", "FC6", "CP5", "CP6", "TP9", "TP10", "EOG", "ECG"]
