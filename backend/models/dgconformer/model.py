"""DGConformer: DGCNN spatial encoder + Conformer temporal encoder for EEG emotion recognition."""

from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class DynamicEdgeConv(nn.Module):
    """Dynamic graph convolution with kNN edges and max pooling over neighbors."""

    def __init__(self, in_channels: int, out_channels: int, k: int = 20):
        super().__init__()
        self.k = k
        self.mlp = nn.Sequential(
            nn.Linear(in_channels * 2, out_channels),
            nn.ReLU(inplace=True),
            nn.Linear(out_channels, out_channels),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [BT, N, F_in] node features for BT independent graphs
        Returns:
            [BT, N, F_out]
        """
        bt, num_nodes, _ = x.shape
        if num_nodes <= 1:
            raise ValueError("DynamicEdgeConv requires at least 2 graph nodes.")

        effective_k = min(self.k, num_nodes - 1)
        # Pairwise distance -> kNN indices: [BT, N, k]
        dist = torch.cdist(x, x)
        _, knn_idx = dist.topk(effective_k + 1, dim=-1, largest=False)
        knn_idx = knn_idx[..., 1:]

        batch_idx = torch.arange(bt, device=x.device).view(bt, 1, 1).expand(bt, num_nodes, effective_k)
        neighbor_feat = x[batch_idx, knn_idx]  # [BT, N, k, F_in]
        center_feat = x.unsqueeze(2).expand_as(neighbor_feat)
        edge_feat = torch.cat([center_feat, neighbor_feat - center_feat], dim=-1)  # [BT, N, k, 2F]

        edge_out = self.mlp(edge_feat)  # [BT, N, k, F_out]
        return edge_out.max(dim=2).values  # [BT, N, F_out]


class DGCNNSpatialEncoder(nn.Module):
    """Apply dynamic EdgeConv on EEG channel graphs for every time step."""

    def __init__(
        self,
        in_channels: int = 5,
        hidden_channels: int = 64,
        k: int = 20,
    ):
        super().__init__()
        self.conv1 = DynamicEdgeConv(in_channels, hidden_channels, k=k)
        self.conv2 = DynamicEdgeConv(hidden_channels, hidden_channels, k=k)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, C, T, F] EEG input (C channels, T time steps, F band features)
        Returns:
            [B, T, C, 64]
        """
        # [B, C, T, F] -> [B, T, C, F]
        x = x.permute(0, 2, 1, 3).contiguous()
        batch_size, time_steps, num_nodes, feat_dim = x.shape

        # Merge batch and time so each slice is one channel graph: [B*T, C, F]
        x = x.view(batch_size * time_steps, num_nodes, feat_dim)
        x = self.conv1(x)  # [B*T, C, 64]
        x = self.conv2(x)  # [B*T, C, 64]

        hidden = x.shape[-1]
        return x.view(batch_size, time_steps, num_nodes, hidden)


class FeedForwardModule(nn.Module):
    """Conformer feed-forward module (returns delta for half-step residual)."""

    def __init__(self, d_model: int, expansion_factor: int = 4, dropout: float = 0.1):
        super().__init__()
        hidden = d_model * expansion_factor
        self.net = nn.Sequential(
            nn.Linear(d_model, hidden),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, L, D] -> delta: [B, L, D]
        return self.net(x)


class ConformerConvModule(nn.Module):
    """Conformer convolution module."""

    def __init__(self, d_model: int, kernel_size: int = 7, dropout: float = 0.1):
        super().__init__()
        padding = kernel_size // 2
        self.layer_norm = nn.LayerNorm(d_model)
        self.pointwise_conv1 = nn.Conv1d(d_model, d_model * 2, kernel_size=1)
        self.depthwise_conv = nn.Conv1d(
            d_model,
            d_model,
            kernel_size=kernel_size,
            padding=padding,
            groups=d_model,
        )
        self.batch_norm = nn.BatchNorm1d(d_model)
        self.pointwise_conv2 = nn.Conv1d(d_model, d_model, kernel_size=1)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, L, D]
        Returns:
            [B, L, D]
        """
        residual = x
        x = self.layer_norm(x)
        # [B, L, D] -> [B, D, L]
        x = x.transpose(1, 2)
        x = self.pointwise_conv1(x)  # [B, 2D, L]
        x = F.glu(x, dim=1)  # [B, D, L]
        x = self.depthwise_conv(x)
        x = self.batch_norm(x)
        x = F.silu(x)
        x = self.pointwise_conv2(x)
        x = self.dropout(x)
        return x.transpose(1, 2) + residual  # [B, L, D]


class ConformerBlock(nn.Module):
    """Single Conformer encoder block."""

    def __init__(
        self,
        d_model: int = 128,
        num_heads: int = 8,
        conv_kernel_size: int = 7,
        dropout: float = 0.1,
        ff_expansion: int = 4,
    ):
        super().__init__()
        self.ff1 = FeedForwardModule(d_model, ff_expansion, dropout)
        self.mha = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.conv_module = ConformerConvModule(d_model, conv_kernel_size, dropout)
        self.ff2 = FeedForwardModule(d_model, ff_expansion, dropout)
        self.norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, L, D]
        x = x + 0.5 * self.ff1(x)
        attn_out, _ = self.mha(x, x, x, need_weights=False)
        x = x + self.dropout(attn_out)
        x = x + self.conv_module(x)
        x = x + 0.5 * self.ff2(x)
        return self.norm(x)  # [B, L, D]


class DGConformer(nn.Module):
    """
    DGConformer: DGCNN spatial graph encoder -> projection -> Conformer temporal encoder -> CLS classifier.

    Paper-style pipeline (not parallel concat):
        spatial graph conv on channels -> temporal tokens -> Conformer -> classification
    """

    def __init__(
        self,
        num_channels: int = 62,
        num_bands: int = 5,
        num_classes: int = 4,
        dgcnn_hidden: int = 64,
        knn_k: int = 20,
        d_model: int = 128,
        num_blocks: int = 4,
        num_heads: int = 8,
        conv_kernel_size: int = 7,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.num_channels = num_channels
        self.num_bands = num_bands
        self.dgcnn_hidden = dgcnn_hidden
        self.d_model = d_model

        self.spatial_encoder = DGCNNSpatialEncoder(
            in_channels=num_bands,
            hidden_channels=dgcnn_hidden,
            k=knn_k,
        )
        self.projection = nn.Linear(num_channels * dgcnn_hidden, d_model)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, d_model))
        self.pos_embedding = nn.Parameter(torch.zeros(1, 512, d_model))
        self.pos_drop = nn.Dropout(dropout)

        self.encoder = nn.ModuleList(
            [
                ConformerBlock(
                    d_model=d_model,
                    num_heads=num_heads,
                    conv_kernel_size=conv_kernel_size,
                    dropout=dropout,
                )
                for _ in range(num_blocks)
            ]
        )
        self.classifier = nn.Linear(d_model, num_classes)
        self._reset_parameters()

    def _reset_parameters(self) -> None:
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.pos_embedding, std=0.02)

    def _apply_positional_encoding(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, L, D], L = T + 1
        seq_len = x.shape[1]
        if seq_len > self.pos_embedding.shape[1]:
            raise ValueError(
                f"Sequence length {seq_len} exceeds pos_embedding capacity "
                f"{self.pos_embedding.shape[1]}. Increase pos_embedding length."
            )
        return x + self.pos_embedding[:, :seq_len, :]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, C, T, F] where C=channels, T=time steps, F=band features
        Returns:
            logits: [B, num_classes]
        """
        batch_size = x.shape[0]

        # 1) DGCNN spatial encoder: [B, C, T, F] -> [B, T, C, 64]
        spatial_feat = self.spatial_encoder(x)

        # 2) Projection: [B, T, C, 64] -> [B, T, C*64] -> [B, T, 128]
        tokens = spatial_feat.reshape(batch_size, spatial_feat.shape[1], -1)
        tokens = self.projection(tokens)  # [B, T, 128]

        # 3) Prepend CLS token: [B, T+1, 128]
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        tokens = torch.cat([cls_tokens, tokens], dim=1)

        # 4) Positional encoding + Conformer encoder
        tokens = self._apply_positional_encoding(tokens)
        tokens = self.pos_drop(tokens)
        for block in self.encoder:
            tokens = block(tokens)  # [B, T+1, 128]

        # 5) CLS classification: [B, 128] -> [B, num_classes]
        cls_repr = tokens[:, 0, :]
        return self.classifier(cls_repr)

