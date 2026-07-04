"""CCA-RMPG core model (classification-only variant)."""

from __future__ import annotations

import torch
import torch.nn as nn

from .layers import (
    CrissCrossAttention,
    Feature_Extractor,
    Label_Classifier,
    RMPG_Module,
    Remove_Band,
)


class CCA_RMPG_NoDA(nn.Module):
    """CCA + RMPG + DCCNN without domain adaptation."""

    def __init__(self, args, device):
        super().__init__()
        self.args = args
        self.device = device

        self.criss_cross_attention = CrissCrossAttention(args=args, device=device)
        self.rmpg = RMPG_Module(
            num_chan=args.channels,
            num_feature=args.bands,
            hidden_graph=getattr(args, "rmpg_hidden", 32),
            num_adj=getattr(args, "rmpg_num_adj", 2),
            layers_graph=getattr(args, "rmpg_layers", [1, 2]),
            graph2token=getattr(args, "rmpg_graph2token", "Linear"),
        )
        self.rmpg_proj = nn.Linear(self.rmpg.hidden_dim, args.conv3_out_dim)
        self.activation = nn.LeakyReLU()
        self.dropout = nn.Dropout(p=0.5)
        self.rmpg_dropout = nn.Dropout(p=0.6)
        self.layer_norm = nn.LayerNorm(args.conv3_out_dim)

        self.removed_band = Remove_Band(args=args)
        self.feature_extractor = Feature_Extractor(args=args, device=device)
        self.label_classifier = Label_Classifier(args=args)

    def forward(self, x):
        # x: [batch, 1, channels, length, bands]
        x, x_attention = self.criss_cross_attention(x)

        x_for_rmpg = x.squeeze(1).permute(0, 2, 1, 3)
        rmpg_out = self.rmpg(x_for_rmpg)
        rmpg_out = self.rmpg_dropout(rmpg_out)
        rmpg_features = self.rmpg_proj(rmpg_out)
        rmpg_features = self.activation(rmpg_features)
        rmpg_features = self.dropout(rmpg_features)
        rmpg_features = self.layer_norm(rmpg_features)

        x_cnn = self.removed_band(x)
        x_cnn = self.feature_extractor(x_cnn)

        rmpg_pooled = rmpg_features.mean(dim=1).unsqueeze(-1).unsqueeze(-1)
        x_combined = x_cnn + rmpg_pooled

        label_pred, tsne_l, fc_2_l, fc_3_l = self.label_classifier(x_combined)
        domain_pred, tsne_d = label_pred, tsne_l

        return label_pred, domain_pred, tsne_l, tsne_d, x_attention, fc_2_l, fc_3_l
