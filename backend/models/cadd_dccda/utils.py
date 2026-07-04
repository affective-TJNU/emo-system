"""Loss helpers for CADD-DCCDA models (inference/training adapter boundary)."""

from __future__ import annotations

import torch.nn as nn


def sum_loss_with_parameter(
    label_pred,
    label_true,
    dc_src_pred,
    dc_src_true,
    dc_tgt_pred,
    dc_tgt_true,
    args,
):
    lc_loss = nn.CrossEntropyLoss()(label_pred, label_true.squeeze().long())
    dc_src_loss = nn.CrossEntropyLoss()(dc_src_pred, dc_src_true.squeeze().long())
    dc_tgt_loss = nn.CrossEntropyLoss()(dc_tgt_pred, dc_tgt_true.squeeze().long())
    total_loss = lc_loss + args.loss_alpha * dc_src_loss + args.loss_beta * dc_tgt_loss
    return lc_loss, dc_src_loss, dc_tgt_loss, total_loss


def sum_loss_with_parameter_without_dd(
    label_pred,
    label_true,
    dc_src_pred,
    dc_src_true,
    dc_tgt_pred,
    dc_tgt_true,
    args,
):
    lc_loss = nn.CrossEntropyLoss()(label_pred, label_true.squeeze().long())
    dc_src_loss = nn.CrossEntropyLoss()(dc_src_pred, dc_src_true.squeeze().long())
    dc_tgt_loss = nn.CrossEntropyLoss()(dc_tgt_pred, dc_tgt_true.squeeze().long())
    total_loss = lc_loss
    return lc_loss, dc_src_loss, dc_tgt_loss, total_loss
