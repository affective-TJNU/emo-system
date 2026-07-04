"""Lightweight brainda-style LOSO report endpoint helper."""

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
from typing import Any, Dict

from .brainda_loso import generate_loso_indices
from .availability import get_metabci_status


def run_loso_summary(config_path: str = "global.config", held_out_subject: int = 0) -> Dict[str, Any]:
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = Path(__file__).resolve().parents[1] / config_file

    parser = ConfigParser()
    parser.read(config_file, encoding="utf-8")
    subject_count = int(parser["seed"].get("sub_num", 15))
    train_subjects, test_subjects, meta = generate_loso_indices(subject_count, held_out_subject)
    status = get_metabci_status()
    return {
        "success": True,
        "module": "brainda",
        "module_available": bool(status["modules"]["brainda"]),
        "fallback_used": False,
        "strategy": "LOSO",
        "split": {
            "train_subjects": train_subjects,
            "test_subjects": test_subjects,
            "train_subject_count": len(train_subjects),
            "test_subject_count": len(test_subjects),
        },
        "meta": meta,
    }
