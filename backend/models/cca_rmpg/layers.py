import torch
import torch.nn as nn
from torch.nn.utils import weight_norm
import numpy as np
import torch.nn.functional as F
from torch.nn import Softmax




def INF(B, H, W, device="cpu"):
    dev = device if isinstance(device, torch.device) else torch.device(device)
    return (
        -torch.diag(torch.full((H,), float("inf"), device=dev), 0)
        .unsqueeze(0)
        .repeat(B * W, 1, 1)
    )


class CrissCrossAttention(nn.Module):
    """ Criss-Cross Attention Module"""
    def __init__(self,args,device):
        super(CrissCrossAttention,self).__init__()
        self.args = args
        self.device =device
        self.query_conv = nn.Conv3d(1, 1, kernel_size=(1, 1, 1))
        self.key_conv = nn.Conv3d(1, 1, kernel_size=(1, 1, 1))
        self.value_conv = nn.Conv3d(1, 1, kernel_size=(1, 1, 1))
        self.softmax = Softmax(dim=3)
        self.INF = INF
        self.gamma = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        m_batchsize, _, channel, length, band = x.size()
        proj_query = self.query_conv(x) # [5, 1, 62, 265, 5]
        proj_query_H = proj_query.permute(0, 1, 2, 4, 3).contiguous().view(m_batchsize * channel, -1, length).permute(0, 2, 1) #[5*62,265, 5]
        proj_query_W = proj_query.permute(0, 1, 3, 2, 4).contiguous().view(m_batchsize*length, -1, channel).permute(0, 2, 1)#[5*265,62,5]
        proj_key = self.key_conv(x)
        proj_key_H = proj_key.permute(0, 1, 2, 4, 3).contiguous().view(m_batchsize*channel, -1, length)#[5*62,5, 265]
        proj_key_W = proj_key.permute(0, 1, 3, 2, 4).contiguous().view(m_batchsize*length, -1, channel)#[5*265, 5, 62]
        proj_value = self.value_conv(x)
        proj_value_H = proj_value.permute(0, 1, 2, 4, 3).contiguous().view(m_batchsize*channel, -1, length)#[5*62,5, 265]
        proj_value_W = proj_value.permute(0, 1, 3, 2, 4).contiguous().view(m_batchsize*length, -1, channel)#[5*265,5, 62]
        #energy_H = (torch.matmul(proj_query_H, proj_key_H)+self.INF(m_batchsize, length, channel)).view(m_batchsize,channel, length, length).permute(0, 2, 1, 3) #[5*62,265,265]-[5, 265, 62, 265]

        a = self.INF(m_batchsize, length, channel, self.device)
        energy_H = (torch.matmul(proj_query_H, proj_key_H) + a).view(m_batchsize,channel, length, length).permute(0, 2, 1, 3)
        energy_W = torch.matmul(proj_query_W, proj_key_W).view(m_batchsize, length, channel, channel) #[5, 265, 62, 62]
        concate = self.softmax(torch.cat([energy_H, energy_W], 3))#[5, 265, 62, 327]
        att_H = concate[:,:,:,0:length].permute(0,2,1,3).contiguous().view(m_batchsize*channel,length,length)
        att_W = concate[:,:,:,length:length+channel].contiguous().view(m_batchsize*length,channel,channel) #[1325, 62, 62]
        out_H = torch.bmm(proj_value_H, att_H.permute(0, 2, 1)).view(m_batchsize,1,channel,-1,length).permute(0,1,2,4,3)
        out_W = torch.bmm(proj_value_W, att_W.permute(0, 2, 1)).view(m_batchsize,1,length,-1,channel).permute(0,1,4,2,3)
        z = self.gamma*(out_H + out_W) + x
        return z, z

def init_conv(conv, glu=True):
    '''
    初始化
    '''
    torch.nn.init.xavier_uniform_(conv.weight)
    if conv.bias is not None:
        conv.bias.data.zero_()



class Remove_Band(nn.Module):
    '''
    为减小后续卷积操作和全连接层的计算量, 通过对频带维度进行1*1*1卷积去掉频带维度
    '''
    def __init__(self, args):
        super(Remove_Band, self).__init__()
        self.args = args
        self.conv = nn.Conv3d(args.bands, 1, (1, 1, 1))
    
    def forward(self, x):
        x = x.permute(0, 4, 2, 3, 1)
        x = self.conv(x)
        x = x.reshape(x.shape[0], x.shape[1], x.shape[2], -1)  # seed: [5,1,62,265] seed_IV;[5, 1, 62, 64]
        return x



class Feature_Extractor(nn.Module):
    '''
    特征提取器: feature extractor
    三层膨胀因果卷积, 由于膨胀因果卷积只在时间维度采用因果卷积, 因此在通道维度卷积核为1
    对于SEED和DEAP卷积核分别为: (1, 8), (1, 5), (1, 3)
    '''
    def __init__(self, args, device):
        super(Feature_Extractor, self).__init__()
        self.args = args
        self.device = device
        #GaussianNoise(1.0)
        if args.dataset == 'SEED':
            # 333
            #self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 3))
            #self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 3), padding=(0, 2), dilation=(1, 3))
            #self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3), padding=(0, 2), dilation=(1, 3))
            # 853
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 8))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 5), padding=(0, 14), dilation=(1, 8))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3), padding=(0, 4), dilation=(1, 5))
            # 888
            #self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 8))
            #self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 8), padding=(0, 6), dilation=(1, 8))
            #self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 8), padding=(0, 6), dilation=(1, 8))
            #358
            #self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 3))
            #self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 5), padding=(0, 4), dilation=(1, 3))
            #self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 8), padding=(0, 14), dilation=(1, 5))
            #555
            #self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 5))
            #self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 5), padding=(0, 2), dilation=(1, 5))
            #self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 5), padding=(0, 2), dilation=(1, 5))
            #CNN
            #self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 8))
            #self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 5), padding=(0, 14))
            #self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3), padding=(0, 4))
        elif args.dataset == 'SEED_IV':
            # self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 3))
            # self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 3),
            #                         padding=(0, 2), dilation=(1, 3))
            # self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3),
            #                         padding=(0, 2), dilation=(1, 3))
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 8))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 5),
                                    padding=(0, 14), dilation=(1, 8))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3),
                                    padding=(0, 4), dilation=(1, 5))
        elif args.dataset == 'DEAP':
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 8))  #UI
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 5),
                                    padding=(0, 14), dilation=(1, 8))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3),
                                    padding=(0, 4), dilation=(1, 5))

            # self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (3, 8))
            # self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (3, 5), 
            #                         padding=(2, 14), dilation=(3, 8))
            # self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (3, 3), 
            #                         padding=(2, 4), dilation=(3, 5))

            #self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 3))   #UD
            #self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 3),
            #                        padding=(0, 2), dilation=(1, 3))
            #self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3),
            #                        padding=(0, 2), dilation=(1, 3))
        
        elif args.dataset == 'SEED_DEAP':
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 3))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 3), 
                                    padding=(0, 2), dilation=(1, 3))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3), 
                                    padding=(0, 2), dilation=(1, 3))
        
        elif args.dataset == 'DEAP_SEED':
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 3))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 3), 
                                    padding=(0, 2), dilation=(1, 3))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3), 
                                    padding=(0, 2), dilation=(1, 3))

        else:
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 5))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 3), 
                                    padding=(0, 4), dilation=(1, 5))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3), 
                                    padding=(0, 4), dilation=(1, 3))
        self.bn_1 = nn.BatchNorm2d(args.conv1_out_dim)
        self.bn_2 = nn.BatchNorm2d(args.conv2_out_dim)
        self.bn_3 = nn.BatchNorm2d(args.conv3_out_dim)
        self.activation = nn.LeakyReLU()

    
    def forward(self, x):
        x = self.conv_1(x)
        x = self.bn_1(x)
        x = self.activation(x)

        x = self.conv_2(x)
        x = self.bn_2(x)
        x = self.activation(x)

        x = self.conv_3(x)
        x = self.bn_3(x)
        x = self.activation(x)#SEED:[5, 24, 62, 252] SEEd_IV:[5, 24, 62, 51]
        return x



def _seed_classifier_pooling_fc(args):
    """SEED 分类器池化：4 导联按时间维池化并动态推断 fc 输入维度。"""
    n_ch = getattr(args, "channels", 62)
    if n_ch <= 4:
        pooling = nn.AvgPool2d((1, 16), padding=(0, 2), stride=(1, 8))
        with torch.no_grad():
            conv3_len = _conv3_time_len(args.length)
            dummy = torch.zeros(1, args.conv3_out_dim, n_ch, conv3_len)
            pooled = pooling(dummy)
            fc_in = int(pooled.reshape(1, -1).shape[1])
        return pooling, fc_in
    pooling = nn.AvgPool2d(16, padding=2, stride=8)
    fc_in = args.conv3_out_dim * 7 * 31
    return pooling, fc_in


def _conv_out_len(length, kernel, padding=0, dilation=1, stride=1):
    return int((length + 2 * padding - dilation * (kernel - 1) - 1) // stride + 1)


def _conv3_time_len(length):
    l1 = _conv_out_len(length, kernel=8)
    l2 = _conv_out_len(l1, kernel=5, padding=14, dilation=8)
    l3 = _conv_out_len(l2, kernel=3, padding=4, dilation=5)
    return l3


# 标签分类器
class Label_Classifier(nn.Module):
    '''
    标签分类器: label classifier

    '''
    def __init__(self, args):
        super(Label_Classifier, self).__init__()
        self.args = args
        if args.dataset == 'SEED':
            self.pooling, fc_in = _seed_classifier_pooling_fc(args)
            self.fc_1 = nn.Linear(fc_in, args.fc1_dim)
        elif args.dataset == 'SEED_IV':
            self.pooling_size = 16
            # self.pooling = nn.AvgPool1d(self.pooling_size, padding=2, stride=8)
            # self.pooling = nn.AvgPool2d((self.pooling_size, 1), padding=(2, 0), stride=(8, 1))
            self.pooling = nn.AvgPool2d(self.pooling_size, padding=2, stride=8)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*32, args.fc1_dim)
            self.fc_1 = nn.Linear(args.conv3_out_dim*7*5, args.fc1_dim)  # length: 64 -> conv -> 49 -> pooling -> 7×5
            # For length=265: nn.Linear(args.conv3_out_dim*7*31, args.fc1_dim)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*7, args.fc1_dim)  # incorrect: should be 7×5 not 7×7
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*3, args.fc1_dim)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*6, args.fc1_dim)
        elif args.dataset == 'DEAP':

            # self.pooling = nn.AvgPool2d((8, 1), padding=(2, 0), stride=(4, 1)) #leave_one_clip_out
            # self.fc_1 = nn.Linear(args.conv3_out_dim*8*3, args.fc1_dim)

            # self.fc_1 = nn.Linear(args.conv3_out_dim*8*56, args.fc1_dim)
            self.pooling = nn.AvgPool2d((8, 16), padding=(2, 4), stride=(4, 8))
            self.fc_1 = nn.Linear(args.conv3_out_dim*8*6, args.fc1_dim)
            '''
            self.pooling = nn.AvgPool2d((8, 16), stride=(4, 8))
            self.fc_1 = nn.Linear(args.conv3_out_dim*5*58, args.fc1_dim)
            '''

        elif args.dataset == 'DREAMER':
            self.pooling = nn.AvgPool2d((4, 16), padding=(1, 4), stride=(2, 8))
            self.fc_1 = nn.Linear(args.conv3_out_dim*5*32, args.fc1_dim)
        elif args.dataset == 'SEED_DEAP':
            self.pooling_size = 4
            self.pooling = nn.AvgPool2d((self.pooling_size, 1), padding=(2, 0), stride=(2, 1))
            self.fc_1 = nn.Linear(args.conv3_out_dim*8*3, args.fc1_dim)
        elif args.dataset == 'DEAP_SEED':
            self.pooling_size = 4
            self.pooling = nn.AvgPool2d((self.pooling_size, 1), padding=(2, 0), stride=(2, 1))
            self.fc_1 = nn.Linear(args.conv3_out_dim*8*3, args.fc1_dim)
        else:
            self.pooling_size = 4
            self.pooling = nn.AvgPool2d(self.pooling_size, padding=2, stride=2)
            self.fc_1 = nn.Linear(args.conv3_out_dim*8*9, args.fc1_dim)
        self.fc_2 = nn.Linear(args.fc1_dim, args.fc2_dim)
        self.fc_3 = nn.Linear(args.fc2_dim, args.nclass)
        self.dropout_1 = nn.Dropout(p=0.2)  # 降低正则化，提高学习能力

        self.dropout_2 = nn.Dropout(p=0.2)  # 降低正则化，提高学习能力
        self.activation_1 = nn.LeakyReLU()
        self.activation_2 = nn.LeakyReLU()
        # 移除Softmax，因为CrossEntropyLoss内部已经包含了Softmax
        # self.activation_3 = nn.Softmax(dim=1)
    
    def forward(self, x):
        x = self.pooling(x) #[5, 24, 7, 31]
        x = x.reshape(x.shape[0], -1)
        tsne_out = x
        out = self.fc_1(x)
        out = self.activation_1(out)
        out = self.dropout_1(out)
        out = self.fc_2(out)
        fc_2_out = out
        out_1 = self.activation_2(out)
        out_1 = self.dropout_2(out_1)
        out_1 = self.fc_3(out_1)
        fc_3_out = out_1
        # 移除Softmax激活，直接返回logits
        # out_2 = self.activation_3(out_1)
        return out_1, tsne_out, fc_2_out, fc_3_out


class Domain_Classifier(nn.Module):
    '''
    域判别器: domain classifier
    加入梯度反转层, 在正向传播时不起作用, 在反向传播时梯度取反, 通过特征提取器与域判别器的对抗学习, 混淆源域与目标域的特征分布
    '''

    def __init__(self, args):
        super(Domain_Classifier, self).__init__()
        self.args = args
        if args.dataset == 'SEED':
            self.pooling, fc_in = _seed_classifier_pooling_fc(args)
            self.fc_1 = nn.Linear(fc_in, args.fc1_dim)
        elif args.dataset == 'SEED_IV':
            self.pooling_size = 16
            # self.pooling = nn.AvgPool1d(self.pooling_size, padding=2, stride=8)
            # self.pooling = nn.AvgPool2d((self.pooling_size, 1), padding=(2, 0), stride=(8, 1))
            self.pooling = nn.AvgPool2d(self.pooling_size, padding=2, stride=8)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*32, args.fc1_dim)
            self.fc_1 = nn.Linear(args.conv3_out_dim * 7 * 5, args.fc1_dim)  # length: 64 -> conv -> 49 -> pooling -> 7×5
            # For length=265: nn.Linear(args.conv3_out_dim * 7 * 31, args.fc1_dim)
            # self.fc_1 = nn.Linear(args.conv3_out_dim * 7 * 7, args.fc1_dim)  # incorrect: should be 7×5 not 7×7
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*3, args.fc1_dim)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*6, args.fc1_dim)
        elif args.dataset == 'DEAP':

            self.pooling = nn.AvgPool2d((8, 1), padding=(2, 0), stride=(4, 1))  # Leave_one_clip_out
            self.fc_1 = nn.Linear(args.conv3_out_dim * 8 * 3, args.fc1_dim)
            self.pooling = nn.AvgPool2d((8, 16), padding=(2, 4), stride=(4, 8))
            self.fc_1 = nn.Linear(args.conv3_out_dim * 8 * 6, args.fc1_dim)

            # self.fc_1 = nn.Linear(args.conv3_out_dim*8*56, args.fc1_dim)
            '''
            self.pooling = nn.AvgPool2d((8, 16), stride=(4, 8))
            self.fc_1 = nn.Linear(args.conv3_out_dim*5*58, args.fc1_dim)
            '''
        elif args.dataset == 'DREAMER':
            self.pooling = nn.AvgPool2d((4, 16), padding=(1, 4), stride=(2, 8))
            self.fc_1 = nn.Linear(args.conv3_out_dim * 5 * 32, args.fc1_dim)
        elif args.dataset == 'SEED_DEAP':
            self.pooling_size = 4
            self.pooling = nn.AvgPool2d((self.pooling_size, 1), padding=(2, 0), stride=(2, 1))
            self.fc_1 = nn.Linear(args.conv3_out_dim * 8 * 3, args.fc1_dim)
        elif args.dataset == 'DEAP_SEED':
            self.pooling_size = 4
            self.pooling = nn.AvgPool2d((self.pooling_size, 1), padding=(2, 0), stride=(2, 1))
            self.fc_1 = nn.Linear(args.conv3_out_dim * 8 * 3, args.fc1_dim)
        else:
            self.pooling_size = 4
            self.pooling = nn.AvgPool2d(self.pooling_size, padding=2, stride=2)
            self.fc_1 = nn.Linear(args.conv3_out_dim * 8 * 9, args.fc1_dim)
        self.fc_2 = nn.Linear(args.fc1_dim, args.fc2_dim)
        self.fc_3 = nn.Linear(args.fc2_dim, args.domain_class)
        self.dropout_1 = nn.Dropout(p=0.2)  # 降低正则化，提高学习能力
        self.dropout_2 = nn.Dropout(p=0.2)  # 降低正则化，提高学习能力
        self.activation_1 = nn.LeakyReLU()
        self.activation_2 = nn.LeakyReLU()
        # 移除Softmax，因为CrossEntropyLoss内部已经包含了Softmax
        # self.activation_3 = nn.Softmax(dim=1)

    def forward(self, x):
        # print(x.shape)
        x = self.pooling(x)
        # print(x.shape)
        x = x.reshape(x.shape[0], -1)
        tsne_out = x
        out = self.fc_1(x)
        out = self.activation_1(out)
        out = self.dropout_1(out)
        out = self.fc_2(out)
        out = self.activation_2(out)
        out = self.dropout_2(out)
        out = self.fc_3(out)
        # 移除Softmax激活，直接返回logits
        # out = self.activation_3(out)

        return out, tsne_out









# GRL对抗网络
class AdversarialLayer(nn.Module):
    def __init__(self, args):
        super(AdversarialLayer, self).__init__()
        self.alpha = args.grl_alpha

    def forward(self, x):
        return GradReverseLayer.apply(x, self.alpha)

class GradReverseLayer(torch.autograd.Function):
    """
    梯度反转层的正确实现
    """
    @staticmethod
    def forward(ctx, x, alpha):
        ctx.alpha = alpha
        return x.view_as(x)
    
    @staticmethod
    def backward(ctx, grad_output):
        output = grad_output.neg() * ctx.alpha
        return output, None

def calc_coeff(iter_num, high=1.0, low=0.0, alpha=10.0, max_iter=10000.0):
    return np.float(2.0 * (high - low) / (1.0 + np.exp(-alpha*iter_num / max_iter)) - (high - low) + low)


# ==================== RMPG Module Components ====================
class GraphConvolution(nn.Module):
    """
    Simple GCN layer for RMPG module
    """
    def __init__(self, in_features, out_features, bias=True):
        super(GraphConvolution, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        torch.nn.init.xavier_uniform_(self.weight, gain=1.414)
        if bias:
            self.bias = nn.Parameter(torch.zeros((1, 1, out_features), dtype=torch.float32))
        else:
            self.register_parameter('bias', None)

    def forward(self, x, adj):
        # x: (batch, num_nodes, in_features)
        # adj: (num_nodes, num_nodes)
        support = torch.matmul(x, self.weight)
        if self.bias is not None:
            output = F.relu(torch.matmul(adj, support) - self.bias)
        else:
            output = F.relu(torch.matmul(adj, support))
        return output


class GraphEncoder(nn.Module):
    """
    Graph Encoder for RMPG module
    """
    def __init__(self, num_layers, num_node, in_features, out_features, graph2token='Linear'):
        super(GraphEncoder, self).__init__()
        self.graph2token = graph2token
        assert graph2token in ['Linear', 'AvgPool', 'MaxPool', 'Flatten'], "graph2token type is not supported!"
        
        if graph2token == 'Linear':
            self.tokenizer = nn.Linear(num_node * out_features, out_features)
        else:
            self.tokenizer = None
        
        layers = []
        for i in range(num_layers):
            if i == 0:
                layer = GraphConvolution(in_features, out_features)
            else:
                layer = GraphConvolution(out_features, out_features)
            layers.append(layer)
        self.encoder = nn.ModuleList(layers)

    def forward(self, x, adj):
        # x: (batch, num_nodes, in_features)
        # adj: (num_nodes, num_nodes)
        for layer in self.encoder:
            x = layer(x, adj)
        
        # x after GCN: (batch, num_nodes, out_features) = (B, 62, 64)
        if self.tokenizer is not None:
            x = x.reshape(x.size(0), -1)
            output = self.tokenizer(x)
        else:
            if self.graph2token == 'AvgPool':
                # 平均池化：在节点维度(dim=1)平均
                # 输出: (batch, out_features)
                output = torch.mean(x, dim=1)
            elif self.graph2token == 'MaxPool':
                # 最大池化：在节点维度(dim=1)取最大
                # 输出: (batch, out_features)
                output = torch.max(x, dim=1)[0]
            else:
                # Flatten
                output = x.reshape(x.size(0), -1)
        return output


class RMPG_Module(nn.Module):
    """
    Residual Multi-view Pyramid GCN Module
    Adapted from EmT for integration with CC-DCCDA
    """
    def __init__(self, num_chan=62, num_feature=5, hidden_graph=32, num_adj=2, 
                 layers_graph=[1, 2], graph2token='Linear'):
        super(RMPG_Module, self).__init__()
        
        self.graph2token = graph2token
        self.num_chan = num_chan
        self.hidden_graph = hidden_graph
        
        # Two graph encoders for multi-view learning
        self.GE1 = GraphEncoder(
            num_layers=layers_graph[0], num_node=num_chan, 
            in_features=num_feature, out_features=hidden_graph,
            graph2token=graph2token
        )
        self.GE2 = GraphEncoder(
            num_layers=layers_graph[1], num_node=num_chan,
            in_features=num_feature, out_features=hidden_graph,
            graph2token=graph2token
        )
        
        # Learnable adjacency matrices
        self.adjs = nn.Parameter(torch.FloatTensor(num_adj, num_chan, num_chan), requires_grad=True)
        nn.init.xavier_uniform_(self.adjs)
        
        # 确定实际输出维度（与GraphEncoder的输出维度一致）
        # MaxPool/AvgPool: 输出hidden_graph维度
        # Linear: 输出hidden_graph维度
        # Flatten: 输出num_chan * hidden_graph维度
        if graph2token == 'Flatten':
            final_dim = num_chan * hidden_graph
        else:
            # 所有其他情况（Linear, MaxPool, AvgPool）输出都是hidden_graph
            final_dim = hidden_graph
        
        # Residual connection - 输出维度与GraphEncoder一致
        self.to_GNN_out = nn.Linear(num_chan * num_feature, final_dim, bias=False)
        
        self.hidden_dim = final_dim

    def get_adj(self):
        """Get symmetric adjacency matrices with self-loops"""
        num_nodes = self.adjs.shape[-1]
        adj = F.relu(self.adjs + self.adjs.transpose(2, 1))
        # Add self-loops
        eye = torch.eye(num_nodes).to(self.adjs.device)
        adj = adj + eye
        return adj

    def forward(self, x):
        # x: (batch, num_nodes, num_features) or (batch, sequence, num_nodes, num_features)
        if x.dim() == 4:
            # If input has sequence dimension, flatten it
            b, s, c, f = x.size()
            x = x.reshape(b * s, c, f)
            has_sequence = True
        else:
            has_sequence = False
        
        # Get adjacency matrices
        adjs = self.get_adj()
        
        # Multi-view pyramid residual GNN block
        x_ = x.reshape(x.size(0), -1)
        x_ = self.to_GNN_out(x_)  # Residual connection
        
        # Two graph encoder views
        x1 = self.GE1(x, adjs[0])
        x2 = self.GE2(x, adjs[1])
        
        # Stack and average (pyramid fusion)
        x_out = torch.stack((x_, x1, x2), dim=1)
        x_out = torch.mean(x_out, dim=1)
        
        if has_sequence:
            x_out = x_out.reshape(b, s, -1)
        
        return x_out

