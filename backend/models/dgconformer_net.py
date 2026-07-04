"""DGConformer adapter for emo-system unified training/inference."""

from __future__ import annotations

import copy

import torch
import torch.nn as nn
import torch.nn.functional as F

from models.dgconformer.model import DGConformer


class DGConformerNet(nn.Module):
    """Wrap DGConformer to match emo-system (logits, tsne1, tsne2) interface."""

    def __init__(self, args, device="cpu"):
        super().__init__()
        self.args = args
        channels = int(getattr(args, "channels_num", 62))
        bands = int(getattr(args, "bands", 5))
        nclass = int(getattr(args, "nclass", 3))
        max_time_steps = int(getattr(args, "feature_len", 176)) + 1

        self.core = DGConformer(
            num_channels=channels,
            num_bands=bands,
            num_classes=nclass,
            dgcnn_hidden=int(getattr(args, "dgconformer_hidden", 64)),
            knn_k=int(getattr(args, "dgconformer_knn_k", 20)),
            d_model=int(getattr(args, "dgconformer_d_model", 128)),
            num_blocks=int(getattr(args, "dgconformer_num_blocks", 4)),
            num_heads=int(getattr(args, "dgconformer_num_heads", 8)),
            conv_kernel_size=int(getattr(args, "dgconformer_conv_kernel", 7)),
            dropout=float(getattr(args, "dropout", 0.1)),
        )
        # Ensure positional encoding can cover CLS + full temporal length.
        if self.core.pos_embedding.shape[1] < max_time_steps:
            self.core.pos_embedding = nn.Parameter(
                torch.zeros(1, max_time_steps, self.core.d_model)
            )
            nn.init.trunc_normal_(self.core.pos_embedding, std=0.02)

    def forward(self, x):
        # emo-system batch shape: [B, C, T, bands]
        tsne1 = copy.deepcopy(x.detach()).reshape(x.shape[0], -1)
        logits = self.core(x)  # [B, nclass]
        tsne2 = copy.deepcopy(logits.detach())
        return logits, tsne1, tsne2

    def loss(self, model, pred, label):
        logits = pred[0]
        ce = F.cross_entropy(logits, label)
        w = torch.cat([p.view(-1) for p in model.parameters()])
        l2_loss = model.args.loss2 * torch.sum(torch.abs(w))
        l1_loss = model.args.loss1 * torch.sum(w.pow(2))
        return ce + l1_loss + l2_loss

