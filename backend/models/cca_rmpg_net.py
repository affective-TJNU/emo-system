"""CCA-RMPG adapter for emo-system unified training/inference."""

from __future__ import annotations

import copy
from argparse import Namespace

import torch
import torch.nn as nn
import torch.nn.functional as F

from models.cca_rmpg.models import CCA_RMPG_NoDA


def _build_cca_rmpg_args(args) -> Namespace:
    channels = int(getattr(args, "channels_num", 4))
    length = int(getattr(args, "feature_len", 176))
    return Namespace(
        dataset="SEED",
        bands=int(getattr(args, "bands", 5)),
        channels=channels,
        length=length,
        nclass=int(getattr(args, "nclass", 3)),
        conv1_out_dim=72,
        conv1_H=1,
        conv1_W=8,
        conv2_out_dim=48,
        conv2_H=1,
        conv2_W=5,
        conv3_out_dim=24,
        conv3_H=1,
        conv3_W=3,
        fc1_dim=1024,
        fc2_dim=150,
        loss_alpha=1.0,
        loss_beta=1.0,
        grl_alpha=1.0,
        domain_class=2,
        rmpg_hidden=int(getattr(args, "rmpg_hidden", 32)),
        rmpg_num_adj=int(getattr(args, "rmpg_num_adj", 2)),
        rmpg_layers=getattr(args, "rmpg_layers", [1, 2]),
        rmpg_graph2token=str(getattr(args, "rmpg_graph2token", "Linear")),
    )


class CCA_RMPGNet(nn.Module):
    """Wrap CCA-RMPG to match ATGRNet-style (logits, tsne1, tsne2) interface."""

    def __init__(self, args, device="cpu"):
        super().__init__()
        self.args = args
        self.cca_args = _build_cca_rmpg_args(args)
        device = getattr(args, "device", device)
        self.inner = CCA_RMPG_NoDA(self.cca_args, device)

    @staticmethod
    def _to_model_input(x: torch.Tensor) -> torch.Tensor:
        # emo-system: (B, C, T, bands) -> CCA-RMPG: (B, 1, C, T, bands)
        if x.ndim == 4:
            return x.unsqueeze(1)
        return x

    def forward(self, x):
        x_in = self._to_model_input(x)
        label_pred, *_rest, fc_3_l = self.inner(x_in)
        tsne1 = copy.deepcopy(x.detach()).reshape(x.shape[0], -1)
        tsne2 = copy.deepcopy(fc_3_l.detach())
        return label_pred, tsne1, tsne2

    def loss(self, model, pred, label):
        logits = pred[0]
        ce = F.cross_entropy(logits, label)
        w = torch.cat([p.view(-1) for p in model.parameters()])
        l2_loss = model.args.loss2 * torch.sum(torch.abs(w))
        l1_loss = model.args.loss1 * torch.sum(w.pow(2))
        return ce + l1_loss + l2_loss
