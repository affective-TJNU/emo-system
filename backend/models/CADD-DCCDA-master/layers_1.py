import torch
import torch.nn as nn
from torch.nn.utils import weight_norm
import numpy as np

def init_conv(conv, glu=True):
    '''
    初始化
    '''
    torch.nn.init.xavier_uniform_(conv.weight)
    if conv.bias is not None:
        conv.bias.data.zero_()

class CrossAttention(nn.Module):
    '''
    交叉注意机制: Cross Attention
    输入: (batch_size, 1, channel, length, band)
    Q, K, V初始化: 分别对输入数据进行1次卷积
    QK = Q*(K.T)
    求QK的下三角矩阵设为0
    最后进行分类
    '''
    def __init__(self, args, device):
        super(CrossAttention, self).__init__()
        self.args = args
        self.device = device
        self.conv_1 = nn.Conv3d(1, 1, kernel_size=(1, 1, 1))
        self.conv_2 = nn.Conv3d(1, 1, kernel_size=(1, 1, 1))
        self.conv_3 = nn.Conv3d(1, 1, kernel_size=(1, 1, 1))
        self.activation = nn.Softmax(dim=-1)
        init_conv(self.conv_1)
        init_conv(self.conv_2)
        init_conv(self.conv_3)
    
    def forward(self, x):
        '''
        先channel
        '''
        WQ_c = self.conv_1(x)
        WK_c = self.conv_2(x)
        WV_c = self.conv_3(x)
        WK_c = WK_c.permute(0, 1, 2, 4, 3)
        QK_c = torch.matmul(WK_c, WQ_c)
        QK_c = torch.tril(QK_c)
        QK_c = self.activation(QK_c)
        V_c = torch.matmul(WV_c, QK_c)
        y = V_c + x

        '''
        后time
        '''
        y_l = y.contiguous().permute(0, 1, 3, 2, 4)
        WQ_l = self.conv_1(y_l)
        WK_l = self.conv_2(y_l)
        WV_l = self.conv_3(y_l)
        WK_l = WK_l.permute(0, 1, 2, 4, 3)
        QK_l = torch.matmul(WK_l, WQ_l)
        QK_l = self.activation(QK_l)
        V_l = torch.matmul(WV_l, QK_l)
        V_l = V_l.permute(0, 1, 3, 2, 4)
        z = V_l + y

        return z, z

class Remove_Band(nn.Module):
    '''
    为减小后续卷积操作和全连接层的计算量, 通过对频带维度进行卷积去掉频带维度
    '''
    def __init__(self, args):
        super(Remove_Band, self).__init__()
        self.args = args
        self.conv = nn.Conv3d(args.bands, 1, (1, 1, 1))
    
    def forward(self, x):
        x = x.permute(0, 4, 2, 3, 1)
        x = self.conv(x)
        x = x.reshape(x.shape[0], x.shape[1], x.shape[2], -1)

        return x

class Band_Attention(nn.Module):
    '''
    为减小后续卷积操作和全连接层的计算量, 通过对频带维度求注意力并求和去掉频带维度, 结果不如卷积操作去掉频带维度
    '''
    def __init__(self, args):
        super(Band_Attention, self).__init__()
        self.args = args
        self.pool = nn.AvgPool3d(kernel_size=(args.channels, args.length, 1))
        self.fc = nn.Linear(args.bands, args.bands)
        self.softmax = nn.Softmax(dim=-1)
    
    def forward(self, x):
        x_pool = self.pool(x)
        out = x_pool.reshape(-1, 5)
        out = self.fc(out)
        out = self.softmax(out)
        out = out.reshape(x.shape[0], x.shape[1], 1, x.shape[-1], 1)
        out = torch.Tensor(np.matmul(x.detach().cpu().numpy(), out.detach().cpu().numpy()))
        out = out.reshape(x.shape[0], x.shape[1], x.shape[2], -1).cuda()
        return out

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
        if args.dataset == 'SEED':
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
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 8))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 5), 
                                    padding=(0, 14), dilation=(1, 8))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3), 
                                    padding=(0, 4), dilation=(1, 5))
            # self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (3, 8))
            # self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (3, 5), 
            #                         padding=(2, 14), dilation=(3, 8))
            # self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (3, 3), 
            #                         padding=(2, 4), dilation=(3, 5))
            # self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 3))
            # self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 3), 
            #                         padding=(0, 2), dilation=(1, 3))
            # self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3), 
            #                         padding=(0, 2), dilation=(1, 3))
        
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
        x = self.activation(x)

        return x

class Chomp1d(nn.Module):
    def __init__(self, chomp_size):
        super(Chomp1d, self).__init__()
        self.chomp_size = chomp_size

    def forward(self, x):
        return x[:, :, :-self.chomp_size].contiguous()

class TemporalBlock(nn.Module):
    def __init__(self, n_inputs, n_outputs, kernel_size, stride, dilation, padding, dropout=0.2):
        super(TemporalBlock, self).__init__()
        self.conv1 = weight_norm(nn.Conv1d(n_inputs, n_outputs, kernel_size,
                                           stride=stride, padding=padding, dilation=dilation))
        self.chomp1 = Chomp1d(padding)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)

        self.conv2 = weight_norm(nn.Conv1d(n_outputs, n_outputs, kernel_size,
                                           stride=stride, padding=padding, dilation=dilation))
        self.chomp2 = Chomp1d(padding)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)

        self.net = nn.Sequential(self.conv1, self.chomp1, self.relu1, self.dropout1,
                                 self.conv2, self.chomp2, self.relu2, self.dropout2)
        self.downsample = nn.Conv1d(n_inputs, n_outputs, 1) if n_inputs != n_outputs else None
        self.relu = nn.ReLU()
        self.init_weights()

    def init_weights(self):
        self.conv1.weight.data.normal_(0, 0.01)
        self.conv2.weight.data.normal_(0, 0.01)
        if self.downsample is not None:
            self.downsample.weight.data.normal_(0, 0.01)

    def forward(self, x):
        out = self.net(x)
        res = x if self.downsample is None else self.downsample(x)
        return self.relu(out + res)

class TemporalConvNet(nn.Module):
    def __init__(self, num_inputs, num_channels, kernel_size=2, dropout=0.2):
        super(TemporalConvNet, self).__init__()
        layers = []
        num_levels = len(num_channels)
        for i in range(num_levels):
            dilation_size = 2 ** i
            in_channels = num_inputs if i == 0 else num_channels[i-1]
            out_channels = num_channels[i]
            layers += [TemporalBlock(in_channels, out_channels, kernel_size, stride=1, dilation=dilation_size,
                                     padding=(kernel_size-1) * dilation_size, dropout=dropout)]

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

class TCN_Feature_Extractor(nn.Module):
    def __init__(self, args, device):
        super(TCN_Feature_Extractor, self).__init__()
        self.args = args
        self.device = device
        num_channels = [args.conv1_out_dim, args.conv2_out_dim, args.conv3_out_dim]
        self.tcn = TemporalConvNet(args.channels, num_channels, kernel_size=7)
        # self.tcn = TemporalBlock(args)
        # self.linear = nn.Linear(num_channels[-1], output_size)
        # self.init_weights()

    # def init_weights(self):
    #     self.linear.weight.data.normal_(0, 0.01)

    def forward(self, x):
        x = x.reshape(x.shape[0], x.shape[2], -1)
        # print(x.shape)
        y1 = self.tcn(x)
        # return self.linear(y1[:, :, -1])
        return y1

class Feature_Extractor_Pool(nn.Module):
    def __init__(self, args, device):
        super(Feature_Extractor_Pool, self).__init__()
        self.args = args
        self.device = device
        # self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (args.conv1_H, args.conv1_W))
        # self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (args.conv2_H, args.conv2_W), 
        #                         padding=(((args.conv1_H-1)*(args.conv2_H-1)/2), ((args.conv1_W-1)*(args.conv2_W-1)/2)), dilation=(args.conv1_H, args.conv1_W))
        # self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (args.conv3_H, args.conv3_W), 
        #                         padding=(((args.conv2_H-1)*(args.conv3_H-1)/2), ((args.conv2_W-1)*(args.conv3_W-1)/2)), dilation=(args.conv2_H, args.conv2_W))
        if args.dataset == 'SEED':
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 8))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 5), 
                                    padding=(0, 14), dilation=(1, 8))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3), 
                                    padding=(0, 4), dilation=(1, 5))
        elif args.dataset == 'DEAP':
            '''
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (3, 8))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (3, 5), 
                                    padding=(2, 14), dilation=(3, 8))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (3, 3), 
                                    padding=(2, 4), dilation=(3, 5))'''
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (5, 8))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (5, 5), 
                                    padding=(8, 14), dilation=(5, 8))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (3, 3), 
                                    padding=(4, 4), dilation=(5, 5))
        
        else:
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (5, 5))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (3, 3), 
                                    padding=(4, 4), dilation=(5, 5))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (3, 3), 
                                    padding=(4, 4), dilation=(3, 3))
        self.pool = nn.AvgPool2d((2, 1), stride=(2, 1))
        self.bn_1 = nn.BatchNorm2d(args.conv1_out_dim)
        self.bn_2 = nn.BatchNorm2d(args.conv2_out_dim)
        self.bn_3 = nn.BatchNorm2d(args.conv3_out_dim)
        self.activation = nn.LeakyReLU()
    
    def forward(self, x):
        x = self.conv_1(x)
        x = self.bn_1(x)
        x = self.pool(x)
        x = self.activation(x)

        x = self.conv_2(x)
        x = self.bn_2(x)
        x = self.pool(x)
        x = self.activation(x)

        x = self.conv_3(x)
        x = self.bn_3(x)
        x = self.pool(x)
        x = self.activation(x)

        return x

class Base_Feature_Extractor(nn.Module):
    def __init__(self, args, device):
        super(Base_Feature_Extractor, self).__init__()
        self.args = args
        self.device = device
        # self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (args.conv1_H, args.conv1_W))
        # self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (args.conv2_H, args.conv2_W))
        # self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (args.conv3_H, args.conv3_W))
        if args.dataset == 'SEED':
            # self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 3))
            # self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 3))
            # self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3))
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 8))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 5))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3))
        elif args.dataset == 'DEAP':
            '''
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (3, 8))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (3, 5), 
                                    padding=(2, 14), dilation=(3, 8))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (3, 3), 
                                    padding=(2, 4), dilation=(3, 5))'''
            self.conv_1 = nn.Conv2d(1, args.conv1_out_dim, (1, 8))
            self.conv_2 = nn.Conv2d(args.conv1_out_dim, args.conv2_out_dim, (1, 5), 
                                    padding=(0, 14), dilation=(1, 8))
            self.conv_3 = nn.Conv2d(args.conv2_out_dim, args.conv3_out_dim, (1, 3), 
                                    padding=(0, 4), dilation=(1, 5))
        
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
        x = self.activation(x)

        return x

class Label_Classifier(nn.Module):
    '''
    标签分类器: label classifier

    '''
    def __init__(self, args):
        super(Label_Classifier, self).__init__()
        self.args = args
        if args.dataset == 'SEED':
            self.pooling_size = 16
            # self.pooling = nn.AvgPool1d(self.pooling_size, padding=2, stride=8)
            # self.pooling = nn.AvgPool2d((self.pooling_size, 1), padding=(2, 0), stride=(8, 1))
            self.pooling = nn.AvgPool2d(self.pooling_size, padding=2, stride=8)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*32, args.fc1_dim)
            self.fc_1 = nn.Linear(args.conv3_out_dim*7*31, args.fc1_dim)  # length: 265
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*3, args.fc1_dim)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*6, args.fc1_dim)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*5, args.fc1_dim)    # length: 60
        elif args.dataset == 'DEAP':
            self.pooling = nn.AvgPool2d((8, 16), padding=(2, 4), stride=(4, 8))
            # self.pooling = nn.AvgPool2d((8, 1), padding=(2, 0), stride=(4, 1))
            # self.fc_1 = nn.Linear(args.conv3_out_dim*8*3, args.fc1_dim)
            self.fc_1 = nn.Linear(args.conv3_out_dim*8*6, args.fc1_dim)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*8*56, args.fc1_dim)
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
        self.dropout_1 = nn.Dropout(p=0.3)
        self.dropout_2 = nn.Dropout(p=0.3)
        self.activation_1 = nn.LeakyReLU()
        self.activation_2 = nn.LeakyReLU()
        self.activation_3 = nn.Softmax(dim=1)
    
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
        fc_2_out = out
        out_1 = self.activation_2(out)
        out_1 = self.dropout_2(out_1)
        out_1 = self.fc_3(out_1)
        fc_3_out = out_1
        out_2 = self.activation_3(out_1)

        return out_2, tsne_out, fc_2_out, fc_3_out

class Label_Classifier_NonPool(nn.Module):
    def __init__(self, args):
        super(Label_Classifier_NonPool, self).__init__()
        self.args = args
        if args.dataset == 'SEED':
            self.pooling = nn.AvgPool2d((1, 16), padding=(0, 2), stride=(1, 8))
            self.fc_1 = nn.Linear(args.conv3_out_dim*7*31, args.fc1_dim)
        elif args.dataset == 'DEAP':
            self.fc_1 = nn.Linear(args.conv3_out_dim*5*59, args.fc1_dim)
            '''
            self.pooling = nn.AvgPool2d((8, 16), stride=(4, 8))
            self.fc_1 = nn.Linear(args.conv3_out_dim*5*58, args.fc1_dim)
            '''
        elif args.dataset == 'DREAMER':
            self.fc_1 = nn.Linear(args.conv3_out_dim*5*32, args.fc1_dim)
        else:
            self.fc_1 = nn.Linear(args.conv3_out_dim*6*9, args.fc1_dim)
        self.fc_2 = nn.Linear(args.fc1_dim, args.fc2_dim)
        self.fc_3 = nn.Linear(args.fc2_dim, args.nclass)
        self.dropout_1 = nn.Dropout(p=0.3)
        self.dropout_2 = nn.Dropout(p=0.3)
        self.activation_1 = nn.LeakyReLU()
        self.activation_2 = nn.LeakyReLU()
        self.activation_3 = nn.Softmax(dim=1)
    
    def forward(self, x):
        x = self.pooling(x)
        # print(x.shape)
        x = x.reshape(x.shape[0], -1)
        x = self.fc_1(x)
        x = self.activation_1(x)
        x = self.dropout_1(x)
        x = self.fc_2(x)
        x = self.activation_2(x)
        x = self.dropout_2(x)
        x = self.fc_3(x)
        x = self.activation_3(x)

        return x

class Domain_Classifier(nn.Module):
    '''
    域判别器: domain classifier
    加入梯度反转层, 在正向传播时不起作用, 在反向传播时梯度取反, 通过特征提取器与域判别器的对抗学习, 混淆源域与目标域的特征分布
    '''
    def __init__(self, args):
        super(Domain_Classifier, self).__init__()
        self.args = args
        if args.dataset == 'SEED':
            self.pooling_size = 16
            # self.pooling = nn.AvgPool1d(self.pooling_size, padding=2, stride=8)
            # self.pooling = nn.AvgPool2d((self.pooling_size, 1), padding=(2, 0), stride=(8, 1))
            self.pooling = nn.AvgPool2d(self.pooling_size, padding=2, stride=8)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*32, args.fc1_dim)
            self.fc_1 = nn.Linear(args.conv3_out_dim*7*31, args.fc1_dim)  # length: 265
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*3, args.fc1_dim)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*6, args.fc1_dim)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*7*5, args.fc1_dim)    # length: 60
        elif args.dataset == 'DEAP':
            self.pooling = nn.AvgPool2d((8, 16), padding=(2, 4), stride=(4, 8))
            # self.pooling = nn.AvgPool2d((8, 1), padding=(2, 0), stride=(4, 1))
            # self.fc_1 = nn.Linear(args.conv3_out_dim*8*3, args.fc1_dim)
            self.fc_1 = nn.Linear(args.conv3_out_dim*8*6, args.fc1_dim)
            # self.fc_1 = nn.Linear(args.conv3_out_dim*8*56, args.fc1_dim)
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
        self.fc_3 = nn.Linear(args.fc2_dim, args.domain_class)
        self.dropout_1 = nn.Dropout(p=0.3)
        self.dropout_2 = nn.Dropout(p=0.3)
        self.activation_1 = nn.LeakyReLU()
        self.activation_2 = nn.LeakyReLU()
        self.activation_3 = nn.Softmax(dim=1)
    
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
        out = self.activation_3(out)

        return out, tsne_out

class Domain_Classifier_NonPool(nn.Module):
    def __init__(self, args):
        super(Domain_Classifier_NonPool, self).__init__()
        self.args = args
        if args.dataset == 'SEED':
            self.pooling = nn.AvgPool2d((1, 16), padding=(0, 2), stride=(1, 8))
            self.fc_1 = nn.Linear(args.conv3_out_dim*7*31, args.fc1_dim)
        elif args.dataset == 'DEAP':
            self.fc_1 = nn.Linear(args.conv3_out_dim*5*59, args.fc1_dim)
            '''
            self.pooling = nn.AvgPool2d((8, 16), stride=(4, 8))
            self.fc_1 = nn.Linear(args.conv3_out_dim*5*58, args.fc1_dim)
            '''
        elif args.dataset == 'DREAMER':
            self.fc_1 = nn.Linear(args.conv3_out_dim*5*32, args.fc1_dim)
        else:
            self.fc_1 = nn.Linear(args.conv3_out_dim*6*9, args.fc1_dim)
        self.fc_2 = nn.Linear(args.fc1_dim, args.fc2_dim)
        self.fc_3 = nn.Linear(args.fc2_dim, args.domain_class)
        self.dropout_1 = nn.Dropout(p=0.3)
        self.dropout_2 = nn.Dropout(p=0.3)
        self.activation_1 = nn.LeakyReLU()
        self.activation_2 = nn.LeakyReLU()
        self.activation_3 = nn.Softmax(dim=1)
    
    def forward(self, x):
        x = self.pooling(x)
        # print(x.shape)
        x = x.reshape(x.shape[0], -1)
        x = self.fc_1(x)
        x = self.activation_1(x)
        x = self.dropout_1(x)
        x = self.fc_2(x)
        x = self.activation_2(x)
        x = self.dropout_2(x)
        x = self.fc_3(x)
        x = self.activation_3(x)

        return x

class AdversarialLayer(nn.Module):
    def __init__(self, args):
        super(AdversarialLayer, self).__init__()
        self.alpha = args.grl_alpha

    def forward(self, x):

        return x.view_as(x)

    def backward(self, grad_output):
        output = grad_output.neg() * self.alpha

        return output