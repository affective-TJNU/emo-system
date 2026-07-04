"""Central model registry for emo-system."""

from __future__ import annotations

from typing import Any, Dict, List, Type

import torch.nn as nn

from ATGRNet import ATGRNet
from models.cadd_dccnn_net import CADD_DCCNNNet
from models.cca_rmpg_net import CCA_RMPGNet
from models.dgconformer_net import DGConformerNet
from models.eegmatch_net import EEGMatchNet

MODEL_REGISTRY: Dict[str, Type[nn.Module]] = {
    "CADD_DCCNN": CADD_DCCNNNet,
    "CCA_RMPG": CCA_RMPGNet,
    "DGConformer": DGConformerNet,
    "EEGMatch": EEGMatchNet,
    "ATGRNet": ATGRNet,
}

MODEL_LABELS: Dict[str, str] = {
    "CADD_DCCNN": "CADD_DCCNN",
    "CCA_RMPG": "CCA-RMPG",
    "DGConformer": "DGConformer",
    "EEGMatch": "EEGMatch",
    "ATGRNet": "ATGRNet",
}

MODEL_ALIASES: Dict[str, str] = {
    "CADD": "CADD_DCCNN",
    "cadd": "CADD_DCCNN",
    "D3CC": "CADD_DCCNN",
    "d3cc": "CADD_DCCNN",
    "CCA-RMPG": "CCA_RMPG",
    "cca_rmpg": "CCA_RMPG",
    "CCA_RMPG": "CCA_RMPG",
    "cca_stda": "CCA_RMPG",
    "eegmatch": "EEGMatch",
    "dgconformer": "DGConformer",
    "DGCONFORMER": "DGConformer",
}

DEFAULT_FEATURE_TYPE = "de_comp_4ch_1p5s"


def normalize_model_name(model_name: str) -> str:
    key = (model_name or "CADD_DCCNN").strip()
    return MODEL_ALIASES.get(key, key)


def list_models() -> List[Dict[str, str]]:
    return [
        {"value": name, "label": MODEL_LABELS.get(name, name)}
        for name in ("CADD_DCCNN", "CCA_RMPG", "DGConformer", "EEGMatch", "ATGRNet")
    ]


def build_model(model_name: str, args: Any) -> nn.Module:
    normalized = normalize_model_name(model_name)
    if normalized not in MODEL_REGISTRY:
        supported = ", ".join(MODEL_REGISTRY)
        raise ValueError(f"Unsupported model '{model_name}'. Supported: {supported}")
    device = getattr(args, "device", "cpu")
    return MODEL_REGISTRY[normalized](args, device=device)
