# -*- coding: utf-8 -*-
# SEED Emotion Dataset Demo — load all 15 subjects
#
# Usage:
#   cd emo-system/MetaBCI-master
#   SEED_EMOTION_DATA_DIR=../backend/seed/Preprocessed_EEG \
#   SEED_EMOTION_ROOT=../backend/seed \
#   PYTHONPATH=. python demos/seed_emotion_demo.py

import json
import os
from pathlib import Path

from metabci.brainda.datasets import SEEDEmotionDataset
from metabci.brainda.datasets.seed_emotion import (
    summarize_seed_dataset,
    verify_seed_dataset_files,
)


def _default_seed_root() -> Path:
    env_root = os.environ.get("SEED_EMOTION_ROOT")
    if env_root:
        return Path(env_root)

    project_seed = Path(__file__).resolve().parents[2] / "backend" / "seed"
    if project_seed.exists():
        return project_seed

    return Path("./seed")


def main():
    seed_root = _default_seed_root()
    raw_data_dir = os.environ.get("SEED_EMOTION_DATA_DIR")
    if raw_data_dir is None:
        candidate = seed_root / "Preprocessed_EEG"
        if candidate.exists():
            raw_data_dir = str(candidate)

    dataset = SEEDEmotionDataset(
        raw_data_dir=raw_data_dir,
        seed_root=seed_root,
    )

    print(dataset)
    print(f"\nRegistered subjects ({len(dataset.subjects)}): {dataset.subjects}")

    print("\nFile check:")
    print(json.dumps(verify_seed_dataset_files(dataset), indent=2))

    print("\nLoading all subjects via get_all_data() ...")
    data = dataset.get_all_data()

    total_trials = 0
    for subject_id in dataset.subjects:
        sessions = data[subject_id]
        session_count = len(sessions)
        trial_count = sum(len(runs) for runs in sessions.values())
        total_trials += trial_count
        first_raw = next(iter(next(iter(sessions.values())).values()))
        shape = first_raw.get_data().shape
        print(
            f"  subject {subject_id:2d}: {session_count} sessions, "
            f"{trial_count:2d} trials, shape {shape}"
        )

    print(
        f"\nLoaded {len(data)} subjects, "
        f"{total_trials} trials total "
        f"(expected {len(dataset.subjects) * dataset.session_num * dataset.trial_num})"
    )

    print("\nSummary:")
    print(json.dumps(summarize_seed_dataset(dataset, subjects=[1]), indent=2))


if __name__ == "__main__":
    main()
