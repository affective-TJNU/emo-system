# -*- coding: utf-8 -*-
"""
Emotion recognition paradigm for SEED-like datasets.
"""
from .base import BaseParadigm


class Emotion(BaseParadigm):
    """Passive emotion elicitation paradigm (SEED)."""

    def is_valid(self, dataset) -> bool:
        return dataset.paradigm == "emotion"
