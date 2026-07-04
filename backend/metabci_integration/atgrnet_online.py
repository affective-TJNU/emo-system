"""Load ATGRNet checkpoints for brainflow online inference."""

from __future__ import annotations

import json
import logging
import os
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BACKEND_DIR / "results"
LATEST_TRAINING_FILE = RESULTS_DIR / "latest_training.json"
MODEL_CHECKPOINTS_FILE = RESULTS_DIR / "model_checkpoints.json"
MODEL_BASENAME = "model_best.pth"
META_BASENAME = "training_meta.json"

CLASS_INDEX_TO_EMOTION = {
    0: "negative",
    1: "neutral",
    2: "positive",
}


def _args_to_meta(args: Any) -> Dict[str, Any]:
    keys = [
        "model",
        "nclass",
        "channels_num",
        "feature_len",
        "windows_num",
        "dropout",
        "graph_out",
        "attention_out",
        "spp",
        "num_levels",
        "kadj",
        "se_squeeze_ratio",
        "graph_readout_dim",
        "domain_class",
        "adj_num",
        "tcn_hidden",
        "tcn_layers",
        "pooling_size",
        "grl_alpha",
        "rsr",
        "k_ratio",
        "loss_beta",
        "loss1",
        "loss2",
        "device",
        "cur_sub_index",
        "feature_type",
        "dataset",
        "bands",
        "have_domain",
        "raw_len",
        "batch_size",
        "eegmatch_use_std",
        "eegmatch_hidden_1",
        "eegmatch_hidden_2",
        "eegmatch_input_dim",
    ]
    meta: Dict[str, Any] = {}
    for key in keys:
        if hasattr(args, key):
            meta[key] = getattr(args, key)
    return meta


def _meta_to_args(meta: Dict[str, Any]) -> Namespace:
    payload = dict(meta)
    payload.setdefault("device", "cpu")
    payload.setdefault("model", "ATGRNet")
    payload.setdefault("nclass", 3)
    payload.setdefault("channels_num", 4)
    payload.setdefault("feature_len", 176)
    payload.setdefault("windows_num", 12)
    payload.setdefault("dropout", 0.5)
    payload.setdefault("graph_out", 128)
    payload.setdefault("attention_out", 256)
    payload.setdefault("spp", True)
    payload.setdefault("num_levels", 3)
    payload.setdefault("kadj", 3)
    payload.setdefault("se_squeeze_ratio", 4)
    payload.setdefault("graph_readout_dim", 256)
    payload.setdefault("domain_class", 15)
    payload.setdefault("adj_num", 5)
    payload.setdefault("tcn_hidden", 30)
    payload.setdefault("tcn_layers", 3)
    payload.setdefault("pooling_size", 1)
    payload.setdefault("grl_alpha", 1.0)
    payload.setdefault("rsr", 1)
    payload.setdefault("k_ratio", 6)
    payload.setdefault("loss_beta", 1.0)
    payload.setdefault("loss1", 5e-6)
    payload.setdefault("loss2", 1e-4)
    payload.setdefault("cur_sub_index", 0)
    payload.setdefault("feature_type", "de_comp_4ch_1p5s")
    payload.setdefault("dataset", "seed")
    payload.setdefault("bands", 5)
    payload.setdefault("have_domain", False)
    payload.setdefault("raw_len", 300)
    payload.setdefault("batch_size", 1)
    payload.setdefault("eegmatch_use_std", 0)
    payload.setdefault("eegmatch_hidden_1", 128)
    payload.setdefault("eegmatch_hidden_2", 256)
    return Namespace(**payload)


def save_training_artifact(
    state_dict: Dict[str, Any],
    args: Any,
    max_acc: float,
) -> Dict[str, str]:
    """Persist best checkpoint + metadata and update latest_training.json."""
    save_path = Path(getattr(args, "save_path", BACKEND_DIR / "seed"))
    if not save_path.is_absolute():
        cwd_candidate = Path.cwd() / save_path
        if cwd_candidate.exists() or cwd_candidate.parent.exists():
            save_path = cwd_candidate.resolve()
        else:
            save_path = (BACKEND_DIR / save_path).resolve()
    save_path.mkdir(parents=True, exist_ok=True)

    model_path = save_path / MODEL_BASENAME
    meta_path = save_path / META_BASENAME
    torch.save(state_dict, model_path)

    meta = _args_to_meta(args)
    meta.update(
        {
            "max_acc": float(max_acc),
            "save_path": str(save_path.resolve()),
            "model_path": str(model_path.resolve()),
        }
    )
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    latest = {
        "model_path": str(model_path.resolve()),
        "meta_path": str(meta_path.resolve()),
        "save_path": str(save_path.resolve()),
        "max_acc": float(max_acc),
        "model": meta.get("model", "ATGRNet"),
        "feature_type": meta.get("feature_type", "de_comp_4ch_1p5s"),
    }
    LATEST_TRAINING_FILE.write_text(json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8")
    update_model_checkpoint(latest)
    logger.info("Saved model checkpoint: %s (max_acc=%.4f)", model_path, max_acc)
    return latest


def _read_meta_for_path(model_path: str) -> Dict[str, Any]:
    meta_path = Path(model_path).parent / META_BASENAME
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _scan_seed_checkpoints() -> Dict[str, Dict[str, Any]]:
    from models.registry import normalize_model_name

    seed_dir = BACKEND_DIR / "seed"
    found: Dict[str, Dict[str, Any]] = {}
    if not seed_dir.is_dir():
        return found

    for run_dir in seed_dir.iterdir():
        if not run_dir.is_dir():
            continue
        meta_path = run_dir / META_BASENAME
        model_file = run_dir / MODEL_BASENAME
        if not meta_path.is_file() or not model_file.is_file():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            model_name = normalize_model_name(str(meta.get("model", "")))
            if not model_name:
                continue
            mtime = model_file.stat().st_mtime
            prev_mtime = float(found.get(model_name, {}).get("_mtime", 0))
            if prev_mtime >= mtime:
                continue
            found[model_name] = {
                "model": model_name,
                "model_path": str(model_file.resolve()),
                "save_path": str(run_dir.resolve()),
                "meta_path": str(meta_path.resolve()),
                "max_acc": float(meta.get("max_acc", 0)),
                "feature_type": meta.get("feature_type", "de_comp_4ch_1p5s"),
                "_mtime": mtime,
            }
        except Exception as exc:
            logger.warning("Skip checkpoint scan for %s: %s", run_dir, exc)

    for entry in found.values():
        entry.pop("_mtime", None)
    return found


def write_model_checkpoints(checkpoints: Dict[str, Dict[str, Any]]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        key: {k: v for k, v in value.items() if not str(k).startswith("_")}
        for key, value in checkpoints.items()
    }
    MODEL_CHECKPOINTS_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_model_checkpoints(refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    if not refresh and MODEL_CHECKPOINTS_FILE.exists():
        try:
            data = json.loads(MODEL_CHECKPOINTS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data:
                return data
        except Exception as exc:
            logger.warning("Failed to read model checkpoints: %s", exc)

    scanned = _scan_seed_checkpoints()
    if scanned:
        write_model_checkpoints(scanned)
    return scanned


def update_model_checkpoint(latest: Dict[str, Any]) -> None:
    from models.registry import normalize_model_name

    model_name = normalize_model_name(str(latest.get("model", "")))
    if not model_name:
        return
    checkpoints = read_model_checkpoints()
    checkpoints[model_name] = {
        "model": model_name,
        "model_path": latest.get("model_path", ""),
        "save_path": latest.get("save_path", ""),
        "meta_path": latest.get("meta_path", ""),
        "max_acc": float(latest.get("max_acc", 0)),
        "feature_type": latest.get("feature_type", "de_comp_4ch_1p5s"),
    }
    write_model_checkpoints(checkpoints)


def get_model_checkpoint(model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    from models.registry import normalize_model_name

    if not model_name:
        return None
    normalized = normalize_model_name(model_name)
    entry = read_model_checkpoints().get(normalized)
    if not entry:
        return None
    model_path = entry.get("model_path", "")
    if model_path and Path(model_path).exists():
        return entry
    refreshed = read_model_checkpoints(refresh=True).get(normalized)
    if refreshed and refreshed.get("model_path") and Path(refreshed["model_path"]).exists():
        return refreshed
    return None


def read_latest_training() -> Optional[Dict[str, Any]]:
    if not LATEST_TRAINING_FILE.exists():
        return None
    try:
        return json.loads(LATEST_TRAINING_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to read latest training pointer: %s", exc)
        return None


def resolve_model_path(
    model_path: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Optional[str]:
    from models.registry import normalize_model_name

    target_model = normalize_model_name(model_name) if model_name else None

    if model_path and Path(model_path).exists():
        resolved = str(Path(model_path).resolve())
        if target_model:
            meta = _read_meta_for_path(resolved)
            stored_model = normalize_model_name(str(meta.get("model", ""))) if meta else ""
            if stored_model and stored_model != target_model:
                logger.warning(
                    "Ignore mismatched model_path for %s: %s",
                    target_model,
                    model_path,
                )
            else:
                return resolved
        else:
            return resolved

    if target_model:
        entry = get_model_checkpoint(target_model)
        if entry and entry.get("model_path"):
            return str(Path(entry["model_path"]).resolve())

    latest = read_latest_training()
    if latest and latest.get("model_path") and Path(latest["model_path"]).exists():
        latest_model = normalize_model_name(str(latest.get("model", "")))
        if not target_model or latest_model == target_model:
            return latest["model_path"]
    return None


def resolve_model_meta(
    model_path: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Read model name / feature_type from checkpoint metadata."""
    from models.registry import normalize_model_name

    meta: Dict[str, Any] = {
        "model": normalize_model_name(model_name) if model_name else "ATGRNet",
        "feature_type": "de_comp_4ch_1p5s",
        "model_path": "",
    }
    resolved = resolve_model_path(model_path, model_name=model_name)
    meta["model_path"] = resolved or ""
    if not resolved:
        entry = get_model_checkpoint(model_name) if model_name else None
        if entry:
            meta["model"] = normalize_model_name(str(entry.get("model", meta["model"])))
            meta["feature_type"] = entry.get("feature_type", meta["feature_type"])
            meta["max_acc"] = entry.get("max_acc")
            meta["model_path"] = entry.get("model_path", "")
            return meta
        latest = read_latest_training()
        if latest:
            meta["model"] = normalize_model_name(str(latest.get("model", meta["model"])))
            meta["feature_type"] = latest.get("feature_type", meta["feature_type"])
        return meta

    meta_path = Path(resolved).parent / META_BASENAME
    if meta_path.exists():
        stored = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["model"] = normalize_model_name(str(stored.get("model", meta["model"])))
        meta["feature_type"] = stored.get("feature_type", meta["feature_type"])
        meta["max_acc"] = stored.get("max_acc")
    return meta


def _checkpoint_missing_graph_layers(state_dict: Dict[str, Any]) -> bool:
    return not any("graph_layer_g" in key for key in state_dict)


def _infer_eegmatch_input_dim(state_dict: Dict[str, Any], args: Namespace) -> int:
    weight = state_dict.get("feature_net.input_proj.weight")
    if weight is not None and hasattr(weight, "shape") and len(weight.shape) == 2:
        return int(weight.shape[1])
    channels = int(getattr(args, "channels_num", 4))
    bands = int(getattr(args, "bands", 5))
    use_std = bool(getattr(args, "eegmatch_use_std", False))
    return channels * bands * (2 if use_std else 1)


def load_model_bundle(model_path: str) -> Tuple[Any, Namespace, torch.device]:
    """Load any supported model checkpoint for online inference."""
    model_path = Path(model_path)
    meta_path = model_path.parent / META_BASENAME
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta = {"model": "ATGRNet", "nclass": 3, "channels_num": 4, "feature_len": 176}

    args = _meta_to_args(meta)
    model_name = str(getattr(args, "model", meta.get("model", "ATGRNet")))
    from models.registry import build_model, normalize_model_name

    model_name = normalize_model_name(model_name)
    device = torch.device("cpu")
    args.device = "cpu"
    args.batch_size = 1

    state_dict = torch.load(model_path, map_location=device)
    if model_name == "EEGMatch":
        args.eegmatch_input_dim = _infer_eegmatch_input_dim(state_dict, args)
        channels = int(getattr(args, "channels_num", 4))
        bands = int(getattr(args, "bands", 5))
        args.eegmatch_use_std = int(args.eegmatch_input_dim) > channels * bands

    model = build_model(model_name, args).to(device)
    strict = True
    if model_name == "ATGRNet" and _checkpoint_missing_graph_layers(state_dict):
        strict = False
        logger.warning(
            "ATGRNet checkpoint missing graph-layer weights; loading compatible subset (strict=False). "
            "Retrain ATGRNet to persist full graph weights."
        )
    missing, unexpected = model.load_state_dict(state_dict, strict=strict)
    if not strict and missing:
        logger.info("ATGRNet skipped %s missing graph-layer keys during load", len(missing))
    if unexpected:
        logger.warning("Unexpected keys while loading %s: %s", model_name, unexpected[:5])
    model.eval()
    return model, args, device


def load_atgrnet_bundle(model_path: str) -> Tuple[Any, Namespace, torch.device]:
    """Backward-compatible alias for ATGRNet loading."""
    return load_model_bundle(model_path)


def decode_replay_sample_index(
    flat_index: int,
    *,
    n_sessions: int,
    n_trials: int,
) -> Dict[str, int]:
    """Map flattened replay index back to subject/session/trial (1-based IDs for UI)."""
    per_subject = max(1, int(n_sessions) * int(n_trials))
    idx = max(0, int(flat_index))
    subject_index = idx // per_subject
    remainder = idx % per_subject
    session_index = remainder // max(1, int(n_trials))
    trial_index = remainder % max(1, int(n_trials))
    return {
        "subject_index": subject_index,
        "subject_id": subject_index + 1,
        "session_index": session_index,
        "session_id": session_index + 1,
        "trial_index": trial_index,
        "trial_id": trial_index + 1,
        "sample_index": idx,
    }


def load_online_replay_tensors(
    feature_type: str = "de_comp_4ch_1p5s",
    held_out_subject: Optional[int] = None,
    all_subjects: bool = True,
    config_path: str = "global.config",
    raw_data_dir: Optional[str] = None,
) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, Any]]:
    """Flatten SEED trials into ATGRNet-ready samples (N, C, F, B).

    When ``all_subjects`` is True (default), replay all subjects instead of one
    held-out subject only.
    """
    from configparser import ConfigParser
    from .brainda_raw_to_de import ensure_de_features_from_raw

    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = BACKEND_DIR / config_file
    parser = ConfigParser()
    parser.read(config_file, encoding="utf-8")
    seed_root = Path(parser["path"]["seed"])
    if not seed_root.is_absolute():
        seed_root = BACKEND_DIR / seed_root

    if raw_data_dir is None and parser.has_option("path", "raw_data_dir"):
        raw_data_dir = parser["path"]["raw_data_dir"]
    if raw_data_dir and not Path(raw_data_dir).is_absolute():
        raw_data_dir = str((BACKEND_DIR / raw_data_dir).resolve())

    ensure_de_features_from_raw(
        raw_data_dir=raw_data_dir,
        seed_root=seed_root,
        feature_type=feature_type,
    )

    data_file = seed_root / feature_type / "data.pt"
    label_file = seed_root / feature_type / "label.pt"
    X = torch.load(data_file, map_location="cpu")
    y = torch.load(label_file, map_location="cpu")
    if int(y.min()) < 0:
        y = (y + 1).long()
    else:
        y = y.long()

    n_subjects, n_sessions, n_trials = int(X.shape[0]), int(X.shape[1]), int(X.shape[2])
    samples_per_subject = n_sessions * n_trials

    use_all = all_subjects or held_out_subject is None
    if use_all:
        X_flat = X.reshape(-1, X.shape[-3], X.shape[-2], X.shape[-1])
        y_flat = y.reshape(-1)
        replay_scope = f"all_{n_subjects}_subjects"
        replay_subjects = list(range(n_subjects))
    else:
        subject_index = max(0, min(int(held_out_subject), n_subjects - 1))
        X_sub = X[subject_index]
        y_sub = y[subject_index]
        X_flat = X_sub.reshape(-1, X_sub.shape[-3], X_sub.shape[-2], X_sub.shape[-1])
        y_flat = y_sub.reshape(-1)
        replay_scope = f"subject_{subject_index}"
        replay_subjects = [subject_index]

    meta = {
        "replay_scope": replay_scope,
        "all_subjects": use_all,
        "n_subjects": n_subjects,
        "n_sessions": n_sessions,
        "n_trials": n_trials,
        "samples_per_subject": samples_per_subject,
        "total_samples": int(X_flat.shape[0]),
        "replay_subjects": replay_subjects,
        "held_out_subject": None if use_all else replay_subjects[0],
    }
    return X_flat, y_flat, meta


def batch_to_model_input(batch_data: Any, args: Namespace) -> torch.Tensor:
    tensor = torch.as_tensor(batch_data, dtype=torch.float32)
    if tensor.ndim == 4:
        return tensor
    if tensor.ndim == 3:
        return tensor.unsqueeze(0)
    channels = int(getattr(args, "channels_num", 4))
    feature_len = int(getattr(args, "feature_len", 176))
    bands = int(getattr(args, "bands", 5))
    if tensor.ndim == 2:
        if tensor.shape[0] == channels and tensor.shape[1] in (bands, feature_len):
            if tensor.shape[1] == bands:
                expanded = tensor.unsqueeze(1).expand(channels, feature_len, bands)
            else:
                expanded = tensor.unsqueeze(-1).expand(channels, feature_len, bands)
            return expanded.unsqueeze(0)
        if tensor.shape[1] == channels * bands:
            return tensor.reshape(1, channels, 1, bands)
    if tensor.ndim == 1:
        if tensor.numel() == channels * bands:
            tensor = tensor.reshape(channels, bands)
        expanded = tensor.unsqueeze(1).expand(tensor.shape[0], feature_len, tensor.shape[-1])
        return expanded.unsqueeze(0)
    raise ValueError(f"Unsupported online input shape: {tuple(tensor.shape)}")


def predict_emotion_probs(model: Any, batch_input: torch.Tensor) -> Dict[str, float]:
    with torch.no_grad():
        logits = model(batch_input)[0]
        probs = F.softmax(logits, dim=-1).squeeze(0).cpu().numpy()
    return {
        CLASS_INDEX_TO_EMOTION.get(idx, "neutral"): round(float(probs[idx]) * 100.0, 2)
        for idx in range(len(probs))
    }
