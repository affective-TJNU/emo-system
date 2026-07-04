from .layers import *
import torch
import torch.nn as nn
from .utils import sum_loss_with_parameter, sum_loss_with_parameter_without_dd

class Model(nn.Module):
    def __init__(self, args, device):
        super(Model, self).__init__()
        self.args = args
        self.device = device
        self.cross_attention = CrossAttention(args=args, device=device)
        self.remove_band = Remove_Band(args=args)
        self.feature_extractor = Feature_Extractor(args=args, device=device)
        self.label_classifier = Label_Classifier(args=args)
        self.grl = AdversarialLayer(args=args)
        self.domain_classifier = Domain_Classifier(args=args)
    
    def forward(self, x):
        x, x_attention = self.cross_attention(x)
        x = self.remove_band(x)
        x = self.feature_extractor(x)
        x_grl = self.grl(x)
        label_pred, tsne_l, fc_2_l, fc_3_l = self.label_classifier(x)
        domain_pred, tsne_d= self.domain_classifier(x_grl)

        return label_pred, domain_pred, tsne_l, tsne_d, x_attention, fc_2_l, fc_3_l
    
    def loss(self, label_pred, label_true, dc_src_pred=torch.zeros(5,2), dc_src_true=torch.zeros(5,1), dc_tgt_pred=torch.zeros(5,2), dc_tgt_true=torch.zeros(5,1)):
        return sum_loss_with_parameter(label_pred, label_true, dc_src_pred, dc_src_true, dc_tgt_pred, dc_tgt_true, self.args)

class Model_1(nn.Module):
    def __init__(self, args, device):
        super(Model_1, self).__init__()
        self.args = args
        self.device = device
        self.cross_attention = CrossAttention(args=args)
        self.band_attention = Band_Attention(args=args)
        self.feature_extractor = Feature_Extractor(args=args, device=device)
        self.label_classifier = Label_Classifier(args=args)
        self.grl = AdversarialLayer(args=args)
        self.domain_classifier = Domain_Classifier(args=args)
    
    def forward(self, x):
        x, x_attention = self.cross_attention(x)
        x = self.band_attention(x)
        x = self.feature_extractor(x)
        x_grl = self.grl(x)
        label_pred, tsne_l, fc_2_l, fc_3_l = self.label_classifier(x)
        domain_pred, tsne_d= self.domain_classifier(x_grl)

        return label_pred, domain_pred, tsne_l, tsne_d, x_attention, fc_2_l, fc_3_l
    
    def loss(self, label_pred, label_true, dc_src_pred=torch.zeros(5,2), dc_src_true=torch.zeros(5,1), dc_tgt_pred=torch.zeros(5,2), dc_tgt_true=torch.zeros(5,1)):
        return sum_loss_with_parameter(label_pred, label_true, dc_src_pred, dc_src_true, dc_tgt_pred, dc_tgt_true, self.args)

class Model_TCN(nn.Module):
    def __init__(self, args, device):
        super(Model_TCN, self).__init__()
        self.args = args
        self.device = device
        self.cross_attention = CrossAttention(args=args)
        self.remove_band = Remove_Band()
        self.feature_extractor = TCN_Feature_Extractor(args, device)
        self.label_classifier = Label_Classifier(args=args)
        self.grl = AdversarialLayer(args=args)
        self.domain_classifier = Domain_Classifier(args=args)
    
    def forward(self, x):
        x = self.cross_attention(x)
        x = self.remove_band(x)
        x = self.feature_extractor(x)
        x_grl = self.grl(x)
        label_pred = self.label_classifier(x)
        domain_pred = self.domain_classifier(x_grl)

        return label_pred, domain_pred
    
    def loss(self, label_pred, label_true, dc_src_pred=torch.zeros(5,2), dc_src_true=torch.zeros(5,1), dc_tgt_pred=torch.zeros(5,2), dc_tgt_true=torch.zeros(5,1)):
        return sum_loss_with_parameter(label_pred, label_true, dc_src_pred, dc_src_true, dc_tgt_pred, dc_tgt_true, self.args)

class Model_Pool(nn.Module):
    def __init__(self, args, device):
        super(Model_Pool, self).__init__()
        self.args = args
        self.device = device
        self.cross_attention = CrossAttention(args=args)
        self.remove_band = Remove_Band()
        self.feature_extractor = Feature_Extractor_Pool(args=args, device=device)
        self.label_classifier = Label_Classifier_NonPool(args=args)
        self.grl = AdversarialLayer(args=args)
        self.domain_classifier = Domain_Classifier_NonPool(args=args)
    
    def forward(self, x):
        x = self.cross_attention(x)
        x = self.remove_band(x)
        x = self.feature_extractor(x)
        x_grl = self.grl(x)
        label_pred = self.label_classifier(x)
        domain_pred = self.domain_classifier(x_grl)

        return label_pred, domain_pred
    
    def loss(self, label_pred, label_true, dc_src_pred=torch.zeros(5,2), dc_src_true=torch.zeros(5,1), dc_tgt_pred=torch.zeros(5,2), dc_tgt_true=torch.zeros(5,1)):
        return sum_loss_with_parameter(label_pred, label_true, dc_src_pred, dc_src_true, dc_tgt_pred, dc_tgt_true, self.args)

class DANN(nn.Module):
    def __init__(self, args, device):
        super(DANN, self).__init__()
        self.args = args
        self.device = device
        # self.band_attention = Band_Attention(args=args)
        self.removed_band = Remove_Band(args=args)
        self.base_feature_extractor = Base_Feature_Extractor(args=args, device=device)
        self.label_classifier = Label_Classifier(args=args)
        self.grl = AdversarialLayer(args=args)
        self.domain_classifier = Domain_Classifier(args=args)
    
    def forward(self, x):
        x_attention = x
        # x = self.band_attention(x)
        x = self.removed_band(x)
        x = self.base_feature_extractor(x)
        x_grl = self.grl(x)
        label_pred, tsne_l, fc_2_l, fc_3_l = self.label_classifier(x)
        domain_pred, tsne_d= self.domain_classifier(x_grl)

        return label_pred, domain_pred, tsne_l, tsne_d, x_attention, fc_2_l, fc_3_l
    
    def loss(self, label_pred, label_true, dc_src_pred=torch.zeros(5,2), dc_src_true=torch.zeros(5,1), dc_tgt_pred=torch.zeros(5,2), dc_tgt_true=torch.zeros(5,1)):
        return sum_loss_with_parameter(label_pred, label_true, dc_src_pred, dc_src_true, dc_tgt_pred, dc_tgt_true, self.args)

class DANN_CA(nn.Module):
    def __init__(self, args, device):
        super(DANN_CA, self).__init__()
        self.args = args
        self.device = device
        self.cross_attention = CrossAttention(args=args)
        # self.band_attention = Band_Attention(args=args)
        self.removed_band = Remove_Band(args=args)
        self.feature_extractor = Base_Feature_Extractor(args=args, device=device)
        self.label_classifier = Label_Classifier(args=args)
        self.grl = AdversarialLayer(args=args)
        self.domain_classifier = Domain_Classifier(args=args)
    
    def forward(self, x):
        x, x_attention = self.cross_attention(x)
        # x = self.band_attention(x)
        x = self.removed_band(x)
        x = self.feature_extractor(x)
        x_grl = self.grl(x)
        label_pred, tsne_l, fc_2_l, fc_3_l = self.label_classifier(x)
        domain_pred, tsne_d= self.domain_classifier(x_grl)

        return label_pred, domain_pred, tsne_l, tsne_d, x_attention, fc_2_l, fc_3_l
    
    def loss(self, label_pred, label_true, dc_src_pred=torch.zeros(5,2), dc_src_true=torch.zeros(5,1), dc_tgt_pred=torch.zeros(5,2), dc_tgt_true=torch.zeros(5,1)):
        return sum_loss_with_parameter(label_pred, label_true, dc_src_pred, dc_src_true, dc_tgt_pred, dc_tgt_true, self.args)

class DANN_DCCNN(nn.Module):
    def __init__(self, args, device):
        super(DANN_DCCNN, self).__init__()
        self.args = args
        self.device = device
        # self.band_attention = Band_Attention(args=args)
        self.removed_band = Remove_Band(args=args)
        self.feature_extractor = Feature_Extractor(args=args, device=device)
        self.label_classifier = Label_Classifier(args=args)
        self.grl = AdversarialLayer(args=args)
        self.domain_classifier = Domain_Classifier(args=args)
    
    def forward(self, x):
        x_attention = x
        # x = self.band_attention(x)
        x = self.removed_band(x)
        x = self.feature_extractor(x)
        x_grl = self.grl(x)
        label_pred, tsne_l, fc_2_l, fc_3_l = self.label_classifier(x)
        domain_pred, tsne_d= self.domain_classifier(x_grl)

        return label_pred, domain_pred, tsne_l, tsne_d, x_attention, fc_2_l, fc_3_l
    
    def loss(self, label_pred, label_true, dc_src_pred=torch.zeros(5,2), dc_src_true=torch.zeros(5,1), dc_tgt_pred=torch.zeros(5,2), dc_tgt_true=torch.zeros(5,1)):
        return sum_loss_with_parameter(label_pred, label_true, dc_src_pred, dc_src_true, dc_tgt_pred, dc_tgt_true, self.args)

class CA_DCCNN(nn.Module):
    def __init__(self, args, device):
        super(CA_DCCNN, self).__init__()
        self.args = args
        self.device = device
        self.cross_attention = CrossAttention(args=args)
        self.removed_band = Remove_Band(args=args)
        self.feature_extractor = Feature_Extractor(args=args, device=device)
        self.label_classifier = Label_Classifier(args=args)
    
    def forward(self, x):
        x, x_attention = self.cross_attention(x)
        x = self.removed_band(x)
        x = self.feature_extractor(x)
        label_pred, tsne_l, fc_2_l, fc_3_l = self.label_classifier(x)
        domain_pred, tsne_d= label_pred, tsne_l

        return label_pred, domain_pred, tsne_l, tsne_d, x_attention, fc_2_l, fc_3_l
    
    def loss(self, label_pred, label_true):
        return sum_loss_with_parameter_without_dd(label_pred, label_true, torch.zeros(5,2), torch.zeros(5,1), torch.zeros(5,2), torch.zeros(5,1), self.args)