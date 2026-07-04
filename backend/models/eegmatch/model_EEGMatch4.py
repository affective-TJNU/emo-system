"""EEGMatch feature extractor adapted for emo-system unified training."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualBlock(nn.Module):
    """Simple feed-forward residual block."""

    def __init__(self, dim: int, dropout: float = 0.25):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim, dim),
            nn.Dropout(dropout),
        )
        self.norm = nn.LayerNorm(dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.norm(x + self.net(x))


class feature_extractor(nn.Module):
    """Enhanced EEGMatch-style MLP with optional attention and residual blocks."""

    def __init__(
        self,
        hidden_1: int,
        hidden_2: int,
        use_attention: bool = True,
        num_heads: int = 4,
        num_residual_blocks: int = 2,
        use_contrastive: bool = False,
        dropout: float = 0.25,
    ):
        super().__init__()
        self.use_attention = use_attention
        self.use_contrastive = use_contrastive
        # Patched by EEGMatchNet._patch_input_layers after construction.
        self.input_proj = nn.Linear(310, hidden_1)
        self.input_skip = nn.Identity()

        self.attn = (
            nn.MultiheadAttention(hidden_1, num_heads, dropout=dropout, batch_first=True)
            if use_attention
            else None
        )
        self.res_blocks = nn.ModuleList(
            [ResidualBlock(hidden_1, dropout=dropout) for _ in range(num_residual_blocks)]
        )
        self.output = nn.Sequential(
            nn.Linear(hidden_1, hidden_2),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.proj_head = (
            nn.Sequential(nn.Linear(hidden_2, hidden_2), nn.GELU())
            if use_contrastive
            else None
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_proj(x) + self.input_skip(x)
        if self.attn is not None:
            attn_out, _ = self.attn(x.unsqueeze(1), x.unsqueeze(1), x.unsqueeze(1))
            x = x + attn_out.squeeze(1)
        for block in self.res_blocks:
            x = block(x)
        features = self.output(x)
        if self.proj_head is not None:
            return self.proj_head(features)
        return features


class SupConLoss(nn.Module):
    """Supervised contrastive loss (optional, for semi-supervised EEGMatch training)."""

    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(self, features: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        device = features.device
        labels = labels.view(-1, 1)
        mask = torch.eq(labels, labels.T).float().to(device)
        logits = torch.div(torch.matmul(features, features.T), self.temperature)
        logits_mask = torch.ones_like(mask) - torch.eye(mask.shape[0], device=device)
        mask = mask * logits_mask
        exp_logits = torch.exp(logits) * logits_mask
        log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True) + 1e-12)
        mean_log_prob_pos = (mask * log_prob).sum(dim=1) / (mask.sum(dim=1) + 1e-12)
        return -mean_log_prob_pos.mean()
