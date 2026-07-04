"""EEGMatch adapter for emo-system unified training/inference."""

from __future__ import annotations

import copy

import torch
import torch.nn as nn
import torch.nn.functional as F

from models.eegmatch.model_EEGMatch4 import feature_extractor


class EEGMatchNet(nn.Module):
    """Simplified EEGMatch classifier using temporal-mean pooled DE features."""

    def __init__(self, args, device="cpu"):
        super().__init__()
        self.args = args
        channels = int(getattr(args, "channels_num", 4))
        bands = int(getattr(args, "bands", 5))
        base_dim = channels * bands
        use_std = bool(int(getattr(args, "eegmatch_use_std", 0)))
        default_dim = base_dim * 2 if use_std else base_dim
        self.input_dim = int(getattr(args, "eegmatch_input_dim", default_dim))
        self.use_std_pool = use_std or self.input_dim > base_dim
        hidden_1 = int(getattr(args, "eegmatch_hidden_1", 128))
        hidden_2 = int(getattr(args, "eegmatch_hidden_2", 256))
        drop = float(getattr(args, "dropout", 0.25))
        self.feature_net = feature_extractor(
            hidden_1,
            hidden_2,
            use_attention=True,
            num_heads=4,
            num_residual_blocks=2,
            use_contrastive=False,
            dropout=drop,
        )
        self._patch_input_layers(self.input_dim, hidden_1)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_2, 128),
            nn.GELU(),
            nn.Dropout(getattr(args, "dropout", 0.5)),
            nn.Linear(128, int(getattr(args, "nclass", 3))),
        )

    def _patch_input_layers(self, input_dim: int, hidden_1: int) -> None:
        self.feature_net.input_proj = nn.Linear(input_dim, hidden_1)
        self.feature_net.input_skip = (
            nn.Linear(input_dim, hidden_1) if input_dim != hidden_1 else nn.Identity()
        )

    def _flatten_input(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim == 4:
            if self.use_std_pool:
                mean = x.mean(dim=2)
                std = x.std(dim=2, unbiased=False)
                merged = torch.cat([mean, std], dim=1)
                return merged.reshape(merged.shape[0], -1)
            pooled = x.mean(dim=2)
            return pooled.reshape(pooled.shape[0], -1)
        if x.ndim == 2:
            return x
        return x.reshape(x.shape[0], -1)

    def forward(self, x):
        tsne1 = copy.deepcopy(x.detach()).reshape(x.shape[0], -1)
        features = self.feature_net(self._flatten_input(x))
        logits = self.classifier(features)
        tsne2 = copy.deepcopy(features.detach())
        return logits, tsne1, tsne2

    def loss(self, model, pred, label):
        logits = pred[0]
        ce = F.cross_entropy(logits, label)
        w = torch.cat([p.view(-1) for p in model.parameters()])
        l2_loss = model.args.loss2 * torch.sum(torch.abs(w))
        l1_loss = model.args.loss1 * torch.sum(w.pow(2))
        return ce + l1_loss + l2_loss
