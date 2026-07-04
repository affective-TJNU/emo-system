# -*- coding: utf-8 -*-
# SEED Emotion Classification Demo with EEGNet

import os
from pathlib import Path

import numpy as np

from metabci.brainda.algorithms.deep_learning import EEGNet
from metabci.brainda.algorithms.utils.model_selection import (
    generate_kfold_indices,
    match_kfold_indices,
    set_random_seeds,
)
from metabci.brainda.datasets import SEEDEmotionDataset
from metabci.brainda.paradigms import Emotion


def _default_paths():
    seed_root = os.environ.get("SEED_EMOTION_ROOT")
    raw_data_dir = os.environ.get("SEED_EMOTION_DATA_DIR")
    if seed_root is None:
        candidate = Path(__file__).resolve().parents[2] / "backend" / "seed"
        seed_root = str(candidate) if candidate.exists() else "./seed"
    if raw_data_dir is None:
        candidate = Path(seed_root) / "Preprocessed_EEG"
        if candidate.exists():
            raw_data_dir = str(candidate)
    return seed_root, raw_data_dir


seed_root, raw_data_dir = _default_paths()

dataset = SEEDEmotionDataset(raw_data_dir=raw_data_dir, seed_root=seed_root)

paradigm = Emotion(
    channels=["AF3", "AF4", "F3", "F4"],
    events=["positive", "neutral", "negative"],
    intervals=[(0, 1.5)],
    srate=200,
)


def raw_hook(raw, caches):
    raw.filter(1, 50, l_trans_bandwidth=1, h_trans_bandwidth=5, phase="zero-double")
    return raw, caches


paradigm.register_raw_hook(raw_hook)

subjects = list(range(1, 16))
print(f"Dataset: {dataset.dataset_code}, subjects: {subjects}")

X, y, meta = paradigm.get_data(
    dataset,
    subjects=subjects,
    return_concat=True,
    n_jobs=1,
    verbose=False,
)
print(f"Samples: {len(y)}, shape: {X.shape}, classes: {np.unique(y)}")

estimator = EEGNet(X.shape[1], X.shape[2], len(np.unique(y)))

set_random_seeds(38)
kfold = 5
indices = generate_kfold_indices(meta, kfold=kfold)

accs = []
for k in range(kfold):
    train_ind, validate_ind, test_ind = match_kfold_indices(k, meta, indices)
    train_ind = np.concatenate((train_ind, validate_ind))
    p_labels = estimator.fit(X[train_ind], y[train_ind]).predict(X[test_ind])
    accs.append(np.mean(p_labels == y[test_ind]))

print(f"5-fold accuracy: {np.mean(accs):.4f} (+/- {np.std(accs):.4f})")
