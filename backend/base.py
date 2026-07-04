# base.py
import argparse
import datetime
import logging
import os
import random
import numpy as np
import torch.nn.init as init
from configparser import ConfigParser
import torch
from torch import nn
from torch.nn.utils import weight_norm
import torch.nn.functional as F
from configparser import ConfigParser
from torch.utils.data import DataLoader,Dataset





def arg_parse():
    r"""初始化参数 超参"""

    parser = argparse.ArgumentParser(description='GTN')

    # basic parser
    parser.add_argument('--epochs', dest='epochs',
                        type=int, help='num of epoch')
    parser.add_argument('--batch_size', dest="batch_size",
                        type=int, help="batch_size")
    parser.add_argument('--nclass', dest='nclass', type=int,
                        help='number of classification')
    parser.add_argument('--gpu', dest='gpu', type=int, help='number of gpu')
    parser.add_argument('--device', dest='device', help='number of gpu')
    parser.add_argument('--dropout', type=float,  help='Dropout.')
    parser.add_argument("--lr", type=float,  help='learning rate.')
    parser.add_argument("--k", type=int,  help='k fold.')
    parser.add_argument('--seed', type=int, help='random seed')
    parser.add_argument('--train_mode',  help='sub nums',
                        choices=['si', 'sd', 'debug'])
    parser.add_argument('--model', help='model selection')
    parser.add_argument('--save_tsne_cm', type=int,
                        help='save tsne confusion matrix data')
    parser.add_argument('--save_model', type=int, help='save model')
    parser.add_argument('--save_path', help='dataset')
    parser.add_argument('--have_domain', help='have_domain')

    # about sample
    parser.add_argument('--bands', type=int, help='num bands',
                        choices=[0, 1, 2, 3, 4, 5])  # 0 means all bands selected
    parser.add_argument('--dataset', dest='dataset', help='dataset')
    parser.add_argument("--feature_type", help='the feature type',
                        choices=['de', 'psd', 'dasm', 'rasm', 'dcau', 'de_comp_4ch_1p5s'])
    parser.add_argument('--label_type', help='label type',
                        choices=['label', 'valence', 'arousal', 'dominance'])
    parser.add_argument('--channels_num', type=int, help='num channels')
    parser.add_argument('--feature_len', type=int, help='length of features')
    parser.add_argument('--raw_len', type=int, help='length of raw data')
    parser.add_argument('--session', type=int, help='test session')

    # loss
    parser.add_argument('--loss2', type=float, help='L2 Loss parameter.')
    parser.add_argument('--loss1', type=float, help='L1 Loss parameter.')

    # data split
    parser.add_argument("--split_method",  help='data split method')
    parser.add_argument('--cur_sub_index', type=int,
                        help='current subject index')
    parser.add_argument('--cur_session_index', type=int,
                        help='current session index')
    parser.add_argument('--cur_exp_index', type=int,
                        help='current experiment index')
    parser.add_argument('--clip_length', type=int,
                        help='clip length')
    parser.add_argument('--k_fold_nums', type=int,
                        help='k_fold_nums')

    # model parameter
    parser.add_argument('--graph_out', type=int, help='graph layer output dim')
    parser.add_argument('--attention_out', type=int,
                        help='attention layer output dim')
    parser.add_argument('--spp', type=bool, help='is spp method')
    parser.add_argument('--num_levels', type=bool, help='spp num_levels')
    parser.add_argument('--kadj', type=int, help='DGCNN k adj')
    parser.add_argument('--se_squeeze_ratio', type=int,
                        help='se_squeeze_ratio')
    parser.add_argument('--graph_readout_dim', type=int,
                        help='graph readout dim')
    parser.add_argument('--domain_class', type=int,
                        help='domain_class')
    parser.add_argument('--adj_num', type=int,
                        help='adj_num')
    parser.add_argument('--windows_num', type=int,
                        help='windows_num')
    parser.add_argument('--tcn_hidden', type=int,
                        help='tcn_hidden')
    parser.add_argument('--tcn_layers', type=int,
                        help='tcn_layers')
    parser.add_argument('--pooling_size', type=int,
                        help='pooling_size')
    parser.add_argument('--grl_alpha', type=float,
                        help='grl_alpha')
    parser.add_argument('--rsr', type=float,
                        help='rsr')
    parser.add_argument('--k_ratio', type=float,
                        help='k_ratio')
    parser.add_argument('--loss_beta', type=float,
                        help='loss_beta')

    # EEGMatch-specific
    parser.add_argument('--eegmatch_use_std', type=int,
                        help='pool mean+std over time (1=on, 0=mean only)')
    parser.add_argument('--eegmatch_hidden_1', type=int,
                        help='EEGMatch first hidden dim')
    parser.add_argument('--eegmatch_hidden_2', type=int,
                        help='EEGMatch second hidden dim')

    # config path
    parser.add_argument('--config_path', help='config file path')

    parser.set_defaults(

        # basic 配置基本训练参数
        epochs=30,# 训练的总轮数。模型将在整个训练数据集上迭代200次。
        batch_size=12,  # 每批训练数据的样本数量。在每个训练步骤中，使用1个样本进行训练。
        nclass=3,  # 分类任务的类别数。例如，对于情绪分类任务，有3种不同的情绪类别。
        gpu=0,  # 指定使用的GPU编号。0表示使用第一个GPU。
        device='cuda:0',  # 设备类型和编号。'cuda:0'表示使用第一个CUDA支持的GPU。
        dropout=.5,  # Dropout正则化率。设置为0.5表示在训练过程中每个神经元有50%的概率被忽略。
        lr=1e-4,  # 学习率。控制模型参数更新的步长，1e-4表示学习率为0.0001
        k=10,  # 可能是k折交叉验证中的折数。将数据分成10个子集，每次用其中一个子集作为验证集，其余作为训练集。
        seed=3407,  # 随机种子。用于确保实验的可重复性，3407是指定的种子值。
        train_mode='si',  # 训练模式。'sd'可能表示“subject-dependent”或其他特定的训练策略。
        model='ATGRNet',  # 模型名称。指定使用ATGRNet模型进行训练。另一个可能的选择是'MAGCN'。
        save_tsne_cm=0,  # 是否保存t-SNE和混淆矩阵。0表示不保存，1表示保存。
        save_model=0,  # 是否保存训练好的模型。0表示不保存，1表示保存。
        save_path='../backend/',  # 模型和其他文件的保存路径。
        have_domain=False,  # 是否包含域（domain）信息。False表示不包含，True表示包含。

        # sample
        bands=5,  # 频带的数量。在脑电图（EEG）分析中，信号通常被分成多个频带（例如δ波、θ波、α波、β波和γ波）。
        # 指定要使用的数据集名称，可以选择 'seed', 'deap', 'dreamer', 'seed_origin', 'amigos', 'seed_iv', 'seed_iv_adj' 等。
        dataset='seed',  # 使用 SEED 数据集。
        feature_type='de_comp_4ch_1p5s',  # 特征类型。可选值包括：
        # 'de'：差分熵特征（Differential Entropy）
        # 'psd'：功率谱密度（Power Spectral Density）
        # 'dasm'：差分绝对α波谱强度（Differential Absolute Spectrum of α）
        # 'rasm'：相对α波谱强度（Relative α Spectrum）
        # 'dcau'：差分累积熵（Differential Cumulative Entropy）

        label_type='label',  # 标签类型。可选值包括：
        # 'label'：类别标签（如情绪分类）
        # 'valence'：情绪愉悦度（Valence）
        # 'arousal'：情绪唤醒度（Arousal）
        # 'dosminance'：情绪主导性（Dominance）
        channels_num=4,  # EEG 数据中通道的数量。此配置默认使用 AF3/AF4/F3/F4 四导联。
        feature_len=176,  # 每个 trial 内最多 176 个 1.5s 片段。
        raw_len=53001,  # 原始 EEG 信号的长度。在信号处理过程中，原始信号通常会被分割成固定长度的片段。
        session=0,  # EEG 数据的会话编号。对于包含多次实验或记录的数据集，0 表示选择第一个会话的数据。

        # loss
        #loss2=1e-4,  # L2正则化损失项的权重
        #loss1=5e-6,  # L1正则化损失项的权重
        loss1=5e-06,
        loss2=0.0001,

        # split
        split_method='loso',  # 数据分割方法，有以下几种选项：
        # 'by_exp': 按实验分割
        # 'by_sess': 按会话分割
        # 'loso': 留一法（Leave-One-Subject-Out）
        # 'k_fold': k折交叉验证（k-fold cross-validation）
        cur_sub_index=0,  # 当前被试的索引，表示在进行分割时当前处理的被试编号。
        cur_session_index=0,  # 当前会话的索引，表示在进行分割时当前处理的会话编号。
        cur_exp_index=0,  # 当前实验的索引，表示在进行分割时当前处理的实验编号。
        clip_length=1,  # 片段长度，表示将时间序列数据分割成的片段长度。
        k_fold_nums=10,  # k折交叉验证中的k值，表示将数据分割成多少个折进行交叉验证。


        # model parameter
        graph_out=128,  # 图卷积输出维度，表示每个节点在图卷积层后的特征维度。
        attention_out=256,  # 注意力机制输出维度，表示在注意力机制后每个节点的特征维度。
        spp=True,  # 是否使用空间金字塔池化（Spatial Pyramid Pooling），用于处理不同尺度的特征。
        num_levels=3,  # 空间金字塔池化的级别数，决定特征提取的尺度数目。
        kadj=3,  # 邻接矩阵的k值，表示每个节点的k近邻数量，用于构建图结构。
        se_squeeze_ratio=4,  # Squeeze-and-Excitation（SE）模块中的缩放比，用于减少通道维度。
        graph_readout_dim=256,  # 图卷积网络读出层的维度，表示整个图的全局特征维度。
        domain_class=15,  # 域分类任务中的类别数量，用于表示不同的域。
        adj_num=5,  # 用于图卷积中的邻接矩阵数量，表示多图结构的数量。
        windows_num=12,  # 时间窗口数量，表示将时间序列数据分割成多少个窗口进行处理。
        tcn_hidden=30,  # TCN（Temporal Convolutional Network）的隐藏层维度，表示时间卷积网络中的特征维度。
        grl_alpha=1.0,  # 梯度反转层（Gradient Reversal Layer）的参数，用于调整反转的梯度大小，通常用于对抗训练。
        tcn_layers=3,  # TCN层数，表示时间卷积网络的层数。
        pooling_size=1,  # 池化层的尺寸，表示在池化操作中窗口的大小。
        loss_beta=1.0,  # 损失函数中的权重参数，用于调整不同损失项的比例。
        rsr=1,  # 读出层压缩比率，用于在读出层进行特征压缩。
        k_ratio=6,  # 邻接矩阵的稀疏度控制参数，表示保留的最大的边数比率。
        eegmatch_use_std=0,
        eegmatch_hidden_1=128,
        eegmatch_hidden_2=256,
        # config
        config_path='../backend/global.config',
    )

    return parser.parse_args()


def setup_seed(seed=3364):
    r"""设置随机种子"""

    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True


def setup_device(args):
    r"""设置GPU"""

    if torch.cuda.is_available():
        args.device = 'cuda:{}'.format(0)
    else:
        args.device = 'cpu'


def get_time(t1, t2):
    r"""计算时分秒；

    Args:
        t1: 程序开始时的系统时间.
        t2: 程序结束后的系统时间.

    Returns:
        运行时分秒
    """

    run_time = round(t2-t1)
    # 计算时分秒
    hour = run_time//3600
    minute = (run_time-3600*hour)//60
    second = run_time-3600*hour-60*minute
    if hour > 0:
        return f'该程序运行时间：{hour}小时{minute}分钟{second}秒'
    if minute > 0:
        return f'该程序运行时间：{minute}分{second}秒'
    return f'该程序运行时间：{second}秒'


def setup_save_path(args):
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    args.save_path = os.path.join(args.save_path, args.dataset, current_time)
    
    # 为所有模式都创建保存路径和配置日志
    if args.train_mode != 'debug':
        os.makedirs(args.save_path)
        # 检查是否已经有日志配置，如果没有才配置
        if not logging.getLogger().handlers:
            logging.basicConfig(filename=os.path.join(args.save_path, 'log.log'),
                                level=logging.DEBUG, format='%(asctime)s - %(message)s',
                                encoding='utf-8')
    else:
        # debug模式也配置日志，但输出到控制台和文件
        os.makedirs(args.save_path, exist_ok=True)
        # 检查是否已经有日志配置，如果没有才配置
        if not logging.getLogger().handlers:
            # 配置同时输出到控制台和文件
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(message)s',
                handlers=[
                    logging.FileHandler(os.path.join(args.save_path, 'log.log'), encoding='utf-8'),
                    logging.StreamHandler()  # 同时输出到控制台
                ]
            )


def custom_init(tensor, positive=True, distribution='uniform', range=(0, 1)):
    # tensor: a torch.Tensor or a nn.Module
    # positive: a boolean indicating whether to initialize with positive values only
    # distribution: a string indicating the type of distribution to sample from, either 'uniform' or 'normal'
    # range: a tuple indicating the lower and upper bound of the distribution

    # apply the initialization function recursively to every submodule if tensor is a nn.Module
    if isinstance(tensor, nn.Module):
        tensor.apply(lambda t: custom_init(t, positive, distribution, range))
        return tensor

    # check the validity of the arguments
    assert distribution in [
        'uniform', 'normal'], "distribution must be either 'uniform' or 'normal'"
    assert len(
        range) == 2 and range[0] < range[1], "range must be a tuple of two numbers with the first one smaller than the second one"

    # sample from the specified distribution
    if distribution == 'uniform':
        init.uniform_(tensor, range[0], range[1])
    else:
        init.normal_(tensor, range[0], range[1])

    # make sure the values are positive if positive is True
    if positive:
        tensor = torch.abs(tensor)

    return tensor


def laplacian_torch(W, normalized=True, symmetry=True):
    A = W
    if symmetry:
        A = A + torch.transpose(A, 0, 1)
        d = torch.sum(A, 1)
        d = 1 / torch.sqrt(d + 1e-10)
        D = torch.diag_embed(d)
        L = torch.matmul(torch.matmul(D, A), D)
    else:
        d = torch.sum(A, 1)
        d = 1 / torch.sqrt(d + 1e-10)
        D = torch.diag_embed(d)
        L = torch.matmul(torch.matmul(D, A), D)
    return L


def truncated_normal_(tensor, mean=0, std=0.1):
    size = tensor.shape
    tmp = tensor.new_empty(size + (4,)).normal_()
    valid = (tmp < 2) & (tmp > -2)
    ind = valid.max(-1, keepdim=True)[1]
    tensor.data.copy_(tmp.gather(-1, ind).squeeze(-1))
    tensor.data.mul_(std).add_(mean)
    return tensor


def calculate_adj_matrix(model, X):
    # 计算分子部分
    diff = X.unsqueeze(2) - X.unsqueeze(1)  # (batchsize, N, N, D)
    abs_diff = torch.abs(diff)  # (batchsize, N, N, D)
    relu_diff = torch.relu(torch.matmul(
        abs_diff, model.W_t))  # (batchsize, N, N, D)
    exp_diff = torch.exp(torch.sum(relu_diff, dim=3))  # (batchsize, N, N)
    # 计算分母部分
    softmax_denominator = torch.sum(
        exp_diff, dim=2, keepdim=True)  # (batchsize, N, 1)

    # 计算邻接矩阵
    A = torch.mean(exp_diff / softmax_denominator, 0)  # (N, N)

    return A


def normalize_A(A, lmax=2):
    A = F.relu(A)
    N = A.shape[0]
    device = A.device
    A = A*(torch.ones(N, N, device=device)-torch.eye(N, N, device=device))
    A = A+A.T
    d = torch.sum(A, 1)
    d = 1 / torch.sqrt((d + 1e-10))
    D = torch.diag_embed(d)
    L = torch.eye(N, N, device=device)-torch.matmul(torch.matmul(D, A), D)
    Lnorm = (2*L/lmax)-torch.eye(N, N, device=device)
    return Lnorm


def generate_cheby_adj(L, K):
    support = []
    device = L.device
    for i in range(K):
        if i == 0:
            support.append(torch.eye(L.shape[-1], device=device))
        elif i == 1:
            support.append(L)
        else:
            temp = torch.matmul(2*L, support[-1],)-support[-2]
            support.append(temp)
    return support


def generate_non_local_graph(args, feat_trans, H, A, num_edge, num_nodes):
    K = args.K
    # if not args.knn:
    # pdb.set_trace()
    x = F.relu(feat_trans(H))
    # D_ = torch.sigmoid(x@x.t())
    D_ = x@x.t()
    _, D_topk_indices = D_.t().sort(dim=1, descending=True)
    D_topk_indices = D_topk_indices[:, :K]
    D_topk_value = D_.t()[torch.arange(
        D_.shape[0]).unsqueeze(-1).expand(D_.shape[0], K), D_topk_indices]
    edge_j = D_topk_indices.reshape(-1)
    edge_i = torch.arange(
        D_.shape[0]).unsqueeze(-1).expand(D_.shape[0], K).reshape(-1).to(H.device)
    edge_index = torch.stack([edge_i, edge_j])
    edge_value = (D_topk_value).reshape(-1)
    edge_value = D_topk_value.reshape(-1)
    return [edge_index, edge_value]


def set_default_config(args):
    config = ConfigParser()
    config.read(args.config_path, encoding='UTF-8')


def loss_fuction(model, y_pred, y_true):
    """
    计算损失函数

    参数:
    - y_pred: 预测结果
    - y_true: 真实结果

    返回:
    损失值
    """
    if model.args.model == 'svm':
        output = torch.softmax(y_pred, dim=1)  # 将输出转换为概率分布的形式
        # 将目标值从二元分类格式转换为多类别格式
        y_true = 2 * \
            torch.nn.functional.one_hot(
                y_true, num_classes=output.shape[1]).float() - 1
        return torch.mean(torch.clamp(1 - y_pred * y_true, min=0))
    else:
        return loss_with_l1_l2(model, y_pred, y_true)


def loss_with_l1_l2(model, y_pred, y_true):
    focal = nn.CrossEntropyLoss()(y_pred, y_true)
    # w = torch.cat([x.view(-1) for x in model.parameters()])
    # l2_loss = model.args.loss2 * torch.sum(torch.abs(w))
    # l1_loss = model.args.loss1 * torch.sum(w.pow(2))
    total_loss = focal  # + l1_loss + l2_loss
    return total_loss


class MeanAccuracy(object):
    def __init__(self, classes_num):
        super().__init__()
        self.classes_num = classes_num

    def reset(self):
        self._crt_counter = np.zeros(self.classes_num)
        self._gt_counter = np.zeros(self.classes_num)

    def update(self, probs, gt_y):
        pred_y = np.argmax(probs, axis=1)
        for pd_y, gt_y in zip(pred_y, gt_y):
            if pd_y == gt_y:
                self._crt_counter[pd_y] += 1
            self._gt_counter[gt_y] += 1

    def compute(self):
        self._gt_counter = np.maximum(
            self._gt_counter, np.finfo(np.float64).eps)
        accuracy = self._crt_counter / self._gt_counter
        mean_acc = np.mean(accuracy)
        return mean_acc


class Accuracy(object):
    def __init__(self, classes_num):
        super().__init__()
        self.classes_num = classes_num

    def reset(self):
        self._crt_counter = np.zeros(self.classes_num)
        self._gt_counter = np.zeros(self.classes_num)

    def update(self, probs, gt_y):
        pred_y = np.argmax(probs, axis=1)
        for pd_y, gt_y in zip(pred_y, gt_y):
            if pd_y == gt_y:
                self._crt_counter[pd_y] += 1
            self._gt_counter[gt_y] += 1

    def compute(self):
        self._crt_counter = np.sum(self._crt_counter)
        self._gt_counter = np.sum(self._gt_counter)
        acc = self._crt_counter / self._gt_counter
        return acc


class MeanLoss(object):
    def __init__(self, batch_size):
        super(MeanLoss, self).__init__()
        self._batch_size = batch_size

    def reset(self):
        self._sum = 0
        self._counter = 0

    def update(self, loss):
        self._sum += loss * self._batch_size
        self._counter += self._batch_size

    def compute(self):
        return self._sum / self._counter


class EarlyStopping(object):
    def __init__(self, patience):
        super(EarlyStopping, self).__init__()
        self.patience = patience
        self.counter = 0
        self.best_score = None

    def __call__(self, score):
        is_best, is_terminate = True, False
        if self.best_score is None:
            self.best_score = score
        elif self.best_score >= score:
            self.counter += 1
            if self.counter >= self.patience:
                is_terminate = True
            is_best = False
        else:
            self.best_score = score
            self.counter = 0
        return is_best, is_terminate


class AccStd(object):
    def __init__(self, batch_size):
        self.acc_array = []

    def reset(self):
        self.acc_array = []

    def update(self, acc):
        self.acc_array.append(acc)

    def compute(self):
        std = float(torch.FloatTensor(self.acc_array).std())*100
        max_acc = max(self.acc_array)
        return max_acc, std


class TSNE(object):
    def __init__(self, args):
        self.args = args
        self.tsne1_train = []
        self.tsne2_train = []
        self.tsne1_test = []
        self.tsne2_test = []

        self.bset_tsne1_train = []
        self.bset_tsne2_train = []

        self.bset_tsne1_test = []
        self.bset_tsne2_test = []

        self.label_train = []
        self.label_test = []
        self.best_label_train = []
        self.best_label_test = []

    def reset(self):
        self.reset_test()
        self.reset_train()
        self.bset_tsne1_train = []
        self.bset_tsne2_train = []

        self.bset_tsne1_test = []
        self.bset_tsne2_test = []

        self.best_label_train = []
        self.best_label_test = []

    def reset_train(self):
        self.tsne1_train = []
        self.tsne2_train = []
        self.label_train = []

    def reset_test(self):
        self.tsne1_test = []
        self.tsne2_test = []
        self.label_test = []

    def update_train(self, tsne1, tsne2, label):
        self.tsne1_train.append(tsne1)
        self.tsne2_train.append(tsne2)
        self.label_train.append(label)

    def update_test(self, tsne1, tsne2, label):
        self.tsne1_test.append(tsne1)
        self.tsne2_test.append(tsne2)
        self.label_test.append(label)

    def update_best(self, is_best):
        if is_best:
            self.bset_tsne1_train = self.tsne1_train
            self.bset_tsne2_train = self.tsne2_train
            self.bset_tsne1_test = self.tsne1_test
            self.bset_tsne2_test = self.tsne2_test
            self.best_label_train = self.label_train
            self.best_label_test = self.label_test

    def save(self):
        self.bset_tsne1_train = torch.cat(self.bset_tsne1_train, 0)
        self.bset_tsne2_train = torch.cat(self.bset_tsne2_train, 0)
        self.bset_tsne1_test = torch.cat(self.bset_tsne1_test, 0)
        self.bset_tsne2_test = torch.cat(self.bset_tsne2_test, 0)
        # print(self.best_label_train)
        self.best_label_train = torch.from_numpy(
            np.concatenate(self.best_label_train, 0))
        self.best_label_test = torch.from_numpy(
            np.concatenate(self.best_label_test, 0))

        return [self.bset_tsne1_train, self.bset_tsne2_train, self.best_label_train, self.bset_tsne1_test, self.bset_tsne2_test, self.best_label_test]


class Confusion(object):
    def __init__(self, args):
        self.args = args
        self.pre_train = []
        self.true_train = []
        self.pre_test = []
        self.true_test = []

        self.bset_pre_train = []
        self.bset_true_train = []

        self.bset_pre_test = []
        self.bset_true_test = []

    def reset(self):
        self.reset_test()
        self.reset_train()

        self.bset_pre_train = []
        self.bset_true_train = []

        self.bset_pre_test = []
        self.bset_true_test = []

    def reset_train(self):
        self.pre_train = []
        self.true_train = []

    def reset_test(self):
        self.pre_test = []
        self.true_test = []

    def update_train(self, pre, true):
        self.pre_train.append(np.argmax(pre, -1))
        self.true_train.append(true)

    def update_test(self, pre, true):
        self.pre_test.append(np.argmax(pre, -1))
        self.true_test.append(true)

    def update_best(self, is_best):
        if is_best:
            self.bset_pre_train = self.pre_train
            self.bset_true_train = self.true_train
            self.bset_pre_test = self.pre_test
            self.bset_true_test = self.true_test

    def save(self):
        self.bset_pre_train = np.concatenate(self.bset_pre_train, 0)
        self.bset_true_train = np.concatenate(self.bset_true_train, 0)
        self.bset_pre_test = np.concatenate(self.bset_pre_test, 0)
        self.bset_true_test = np.concatenate(self.bset_true_test, 0)

        return [self.bset_pre_train, self.bset_true_train, self.bset_pre_test, self.bset_true_test]


class DataSaver(object):
    def __init__(self, args):

        self.args = args
        self.save_path = args.save_path

    def save_c(self, model, tsne_class):

        if not os.path.exists(os.path.join(self.save_path, 'tsne_class')):
            os.makedirs(os.path.join(self.save_path, 'tsne_class'))
        torch.save(tsne_class, os.path.join(
            self.save_path, 'tsne_class', f'tsne_{self.args.cur_sub_index}.pt'))

    def save_cd(self, model, tsne_class, tsne_domain):

        if not os.path.exists(os.path.join(self.save_path, 'tsne_class')):
            os.makedirs(os.path.join(self.save_path, 'tsne_class'))
        if not os.path.exists(os.path.join(self.save_path, 'tsne_domain')):
            os.makedirs(os.path.join(self.save_path, 'tsne_domain'))

        torch.save(tsne_class, os.path.join(
            self.save_path, 'tsne_class', f'tsne_{self.args.cur_sub_index}.pt'))
        torch.save(tsne_domain, os.path.join(
            self.save_path, 'tsne_domain', f'tsne_{self.args.cur_sub_index}.pt'))







class GraphConvolution(nn.Module):

    def __init__(self, in_channels, out_channels, bias=False, device='cpu'):

        super(GraphConvolution, self).__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.device = device
        self.weight = nn.Parameter(torch.FloatTensor(
            in_channels, out_channels).to(device))
        nn.init.xavier_normal_(self.weight)
        self.bias = None
        if bias:
            self.bias = nn.Parameter(torch.FloatTensor(out_channels).to(device))
            nn.init.zeros_(self.bias)

    def forward(self, x, adj):
        out = torch.matmul(adj, x)
        out = torch.matmul(out, self.weight)
        if self.bias is not None:
            return out + self.bias
        else:
            return out


class Linear(nn.Module):
    def __init__(self, in_channels, out_channels, bias=True):
        super(Linear, self).__init__()
        self.linear = nn.Linear(in_channels, out_channels, bias=bias)
        nn.init.xavier_normal_(self.linear.weight)
        if bias:
            nn.init.zeros_(self.linear.bias)

    def forward(self, inputs):
        return self.linear(inputs)


class SELayer(nn.Module):
    def __init__(self, channel, reduction=16):
        super(SELayer, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        '''
        x:[batch,band_size,H,W]
        '''
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return (x * y.expand_as(x)).type_as(x)


class ReadoutLayer(nn.Module):
    """Graph Readout Layer."""

    def __init__(self, args,
                 input_dim,
                 output_dim,
                 act=nn.ReLU(),
                 dropout_p=0.):
        super(ReadoutLayer, self).__init__()
        self.args = args
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.act = act
        self.dropout_p = dropout_p
        self.dropout = nn.Dropout(self.dropout_p)
        self.att_weight = self.glorot([self.input_dim, 1])
        self.emb_weight = self.glorot([self.input_dim, self.input_dim])
        self.mlp_weight = self.glorot([self.input_dim, self.output_dim])
        self.att_bias = nn.Parameter(torch.zeros(1))
        self.emb_bias = nn.Parameter(torch.zeros(self.input_dim))
        self.mlp_bias = nn.Parameter(torch.zeros(self.output_dim))

    def forward(self, x):  # _ not used
        # soft attention
        att = torch.sigmoid(torch.matmul(x, self.att_weight)+self.att_bias)
        emb = self.act(torch.matmul(x, self.emb_weight)+self.emb_bias)
        # graph summation
        g = att * emb
        g = torch.cat([torch.sum(g, dim=1) + torch.max(g, dim=1)[0]], dim=1)
        # g = self.dropout(g)
        # classification
        output = torch.matmul(g, self.mlp_weight)+self.mlp_bias
        return output

    def glorot(self, shape):
        init_range = np.sqrt(6.0/(shape[0]+shape[1]))
        initial = nn.Parameter(torch.nn.init.uniform_(
            tensor=torch.empty(shape), a=-init_range, b=init_range))
        return initial


class TemporalBlock(nn.Module):
    def __init__(self, n_inputs, n_outputs, kernel_size, stride, dilation, padding, dropout=0.2):
        """
        相当于一个Residual block

        :param n_inputs: int, 输入通道数
        :param n_outputs: int, 输出通道数
        :param kernel_size: int, 卷积核尺寸
        :param stride: int, 步长，一般为1
        :param dilation: int, 膨胀系数
        :param padding: int, 填充系数
        :param dropout: float, dropout比率
        """
        super(TemporalBlock, self).__init__()
        self.conv1 = weight_norm(nn.Conv1d(n_inputs, n_outputs, kernel_size,
                                           stride=stride, padding=padding, dilation=dilation))
        # 经过conv1，输出的size其实是(Batch, input_channel, seq_len + padding)
        self.chomp1 = Chomp1d(padding)  # 裁剪掉多出来的padding部分，维持输出时间步为seq_len
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)

        self.conv2 = weight_norm(nn.Conv1d(n_outputs, n_outputs, kernel_size,
                                           stride=stride, padding=padding, dilation=dilation))
        self.chomp2 = Chomp1d(padding)  # 裁剪掉多出来的padding部分，维持输出时间步为seq_len
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)

        self.net = nn.Sequential(self.conv1, self.chomp1, self.relu1, self.dropout1,
                                 self.conv2, self.chomp2, self.relu2, self.dropout2)
        self.downsample = nn.Conv1d(
            n_inputs, n_outputs, 1) if n_inputs != n_outputs else None
        self.relu = nn.ReLU()
        self.init_weights()

    def init_weights(self):
        """
        参数初始化

        :return:
        """
        self.conv1.weight.data.normal_(0, 0.01)
        self.conv2.weight.data.normal_(0, 0.01)
        if self.downsample is not None:
            self.downsample.weight.data.normal_(0, 0.01)

    def forward(self, x):
        """
        :param x: size of (Batch, input_channel, seq_len)
        :return:
        """
        out = self.net(x)
        res = x if self.downsample is None else self.downsample(x)
        return self.relu(out + res)


class TemporalConvNet(nn.Module):
    def __init__(self, num_inputs, num_channels, kernel_size=2, dropout=0.2):
        """
        TCN，目前paper给出的TCN结构很好的支持每个时刻为一个数的情况，即sequence结构，
        对于每个时刻为一个向量这种一维结构，勉强可以把向量拆成若干该时刻的输入通道，
        对于每个时刻为一个矩阵或更高维图像的情况，就不太好办。

        :param num_inputs: int， 输入通道数
        :param num_channels: list，每层的hidden_channel数，例如[25,25,25,25]表示有4个隐层，每层hidden_channel数为25
        :param kernel_size: int, 卷积核尺寸
        :param dropout: float, drop_out比率
        """
        super(TemporalConvNet, self).__init__()
        layers = []
        num_levels = len(num_channels)
        for i in range(num_levels):
            dilation_size = 2 ** i   # 膨胀系数：1，2，4，8……
            # 确定每一层的输入通道数
            in_channels = num_inputs if i == 0 else num_channels[i-1]
            out_channels = num_channels[i]  # 确定每一层的输出通道数
            layers += [TemporalBlock(in_channels, out_channels, kernel_size, stride=1, dilation=dilation_size,
                                     padding=(kernel_size-1) * dilation_size, dropout=dropout)]

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        """
        输入x的结构不同于RNN，一般RNN的size为(Batch, seq_len, channels)或者(seq_len, Batch, channels)，
        这里把seq_len放在channels后面，把所有时间步的数据拼起来，当做Conv1d的输入尺寸，实现卷积跨时间步的操作，
        很巧妙的设计。

        :param x: size of (Batch, input_channel, seq_len)
        :return: size of (Batch, output_channel, seq_len)
        """
        return self.network(x)


class Chomp1d(nn.Module):
    def __init__(self, chomp_size):
        super(Chomp1d, self).__init__()
        self.chomp_size = chomp_size

    def forward(self, x):
        """
        其实这就是一个裁剪的模块，裁剪多出来的padding
        """
        return x[:, :, :-self.chomp_size].contiguous()


class Chebynet(nn.Module):
    def __init__(self, in_channels, K, out_channels):
        super(Chebynet, self).__init__()
        self.K = K
        self.gc = nn.ModuleList()
        for i in range(K):
            self.gc.append(GraphConvolution(in_channels,  out_channels))

    def forward(self, x, L):
        adj = generate_cheby_adj(L, self.K)
        for i in range(len(self.gc)):
            if i == 0:
                result = self.gc[i](x, adj[i])
            else:
                result += self.gc[i](x, adj[i])
        result = F.relu(result)
        return result




class DataSplit():
    r"""获得划分好的数据集"""

    def __init__(self, args):
        """
        初始化DataSplit类的实例。

        参数:
        - args: 包含配置信息的对象

        返回值:
        无
        """
        self.feature_type = args.feature_type
        self.label_type = args.label_type
        self.args = args
        self.dataset = self.get_dataset_class()

        config = ConfigParser()
        config.read(args.config_path, encoding='UTF-8')

        self.X, self.y = self.load_data(config['path'])
        args.nclass = int(config[args.dataset]['nclass'])
        args.domain_class = int(config[args.dataset]['sub_num'])
        # 划分 self.X_train, self.y_train, self.X_test, self.y_test
        self.data_split(args)

        # 获得dataloader
        self.train_loader = self.get_dataloader(is_train=True)
        self.test_loader = self.get_dataloader(is_train=False)

    def load_data(self, path_set):
        r"""从数据集的文件夹中读取出数据和标签

        参数:
        - path_set: 包含数据集路径的字典

        返回值:
        - X: 数据
        - y: 标签
        """

        if self.args.dataset == 'seed':
            try:
                from metabci_integration.brainda_seed import load_seed_feature_tensors
                X, y, meta = load_seed_feature_tensors(
                    path_set[self.args.dataset], self.feature_type)
                print(f"brainda加载SEED完成: {meta['data_shape']} labels={meta['label_shape']}")
                logging.info(f"brainda加载SEED完成: {meta}")
            except Exception as e:
                print(f"brainda加载SEED失败，回退到torch.load: {e}")
                logging.warning(f"brainda加载SEED失败，回退到torch.load: {e}")
                X = torch.load(os.path.join(
                    path_set[self.args.dataset], f'{self.feature_type}', 'data.pt'))
                y = torch.load(os.path.join(
                    path_set[self.args.dataset], f'{self.feature_type}', 'label.pt'))
        else:
            X = torch.load(os.path.join(
                path_set[self.args.dataset], f'{self.feature_type}', 'data.pt'))
            y = torch.load(os.path.join(
                path_set[self.args.dataset], f'{self.feature_type}', 'label.pt'))

        if self.args.dataset == 'deap':
            y = y[:, :, :, self.get_label_dict(
                self.args.dataset, self.args.label_type)]
        elif self.args.dataset == 'seed' and y.min() < 0:
            # SEED emotion labels are commonly stored as -1/0/1.
            # CrossEntropyLoss expects class indices 0/1/2.
            y = (y + 1).long()
        else:
            y = y.long()

        return X, y

    def data_split(self, args):
        """
        对数据集进行切分:

        参数:

        args: 参数对象,包含切分方法等参数信息

        功能:

        根据切分方法如'by_exp'、'by_sess'等,按受试者、实验或者session等特征划分数据集为训练和测试子集
        将数据集形状改变为(index, channel, feature, band)的形式
        打印日志,记录特征长度和通道数量信息

        返回:

        无返回,但会将训练和测试子集结果赋值给类成员属性:

        self.X_train: 训练子集输入特征
        self.y_train: 训练子集目标变量
        self.X_test: 测试子集输入特征
        self.y_test: 测试子集目标变量
        """

        split_methods = {

            # SD
            'by_exp': lambda: self.split_by_exp(args),
            'by_sess': lambda: self.split_by_sess(args),

            # SI
            'loso': lambda: self.split_loso(args),
            'k_fold': lambda: self.split_k_fold(args),
        }
        self.X_train, self.y_train, self.X_test, self.y_test = split_methods[args.split_method](
        )
        self.X_train, self.y_train = self.reshape_sample(
            self.X_train, self.y_train)
        self.X_test, self.y_test = self.reshape_sample(
            self.X_test, self.y_test)
        if not args.spp:
            args.feature_len = self.X_train.shape[2]
            args.channels_num = self.X_train.shape[1]
        if args.dataset == 'seed_adj' or args.dataset == 'seed_iv_adj':
            args.channels_num = self.X_train[0]['data'].shape[0]
            args.feature_len = self.X_train[0]['data'].shape[1]
        else:
            args.feature_len = self.X_train.shape[2]
            args.channels_num = self.X_train.shape[1]

        print(
            'features length:', args.feature_len, '   ',
            'channels nums:', args.channels_num)
        logging.info(
            f'features length: {args.feature_len}, channels nums: {args.channels_num}')

    def split_by_exp(self, args):
        r"""受试者依赖的按试验留一交叉验证划分

        根据试验进行划分:

        参数:

        无

        功能:

        按当前受试者和实验索引,利用滑动窗口方式划分实验数据
        将对应受试者和实验的输入输出数据分为训练和测试子集

        返回:

        X_train: 输入训练子集
        y_train: 输出训练子集
        X_test: 输入测试子集
        y_test: 输出测试子集
        """

        sub_index = args.cur_sub_index
        exp_index = args.cur_exp_index
        clip_length = args.clip_length

        exp_nums = [i for i in range(self.X.shape[2])]
        # if args.dataset == 'faced':
        #     exp_test = []
        #     exp_test += random.sample(exp_nums[:12], 3)
        #     exp_test += random.sample(exp_nums[12:16], 1)
        #     exp_test += random.sample(exp_nums[16:], 3)
        #     random.shuffle(exp_test)
        # else:
        exp_test = exp_nums[exp_index *
                            clip_length:exp_index * clip_length + clip_length]
        exp_train = [x for x in exp_nums if x not in exp_test]

        # X_train = self.X[sub_index, :, exp_train]
        # X_test = self.X[sub_index, :, exp_test]
        # y_train = self.y[sub_index, :, exp_train]
        # y_test = self.y[sub_index, :, exp_test]

        X_train = self.X[:, :, exp_train]
        X_test = self.X[:, :, exp_test]
        y_train = self.y[:, :, exp_train]
        y_test = self.y[:, :, exp_test]

        return X_train, y_train, X_test, y_test

    def split_by_sess(self, args):
        r"""受试者依赖的按session留一交叉验证划分

        根据session进行划分:

        参数:

        无

        功能:

        按当前受试者和session索引,将数据集分为训练和测试子集
        训练子集包含session索引以外的所有session数据
        测试子集包含指定session索引的数据

        返回:

        X_train: 输入训练子集
        y_train: 输出训练子集
        X_test: 输入测试子集
        y_test: 输出测试子集

        """

        sub_index = args.cur_sub_index
        session_index = args.cur_session_index

        # 动态检测session数量，而不是硬编码为3
        if isinstance(self.X, torch.Tensor):
            # 如果是tensor，检查第二个维度（session维度）
            if len(self.X.shape) >= 2:
                session_count = self.X.shape[1]
            else:
                session_count = 1
        else:
            # 如果是列表，检查第一个被试者的session数量
            if len(self.X) > 0 and isinstance(self.X[0], (list, tuple)):
                session_count = len(self.X[0])
            else:
                session_count = 1

        # 创建session列表
        sess_nums = list(range(session_count))
        
        # 确保session_index在有效范围内
        if session_index >= session_count:
            print(f"警告：session_index {session_index} 超出范围 [0, {session_count-1}]，使用最后一个session")
            session_index = session_count - 1
        
        sess_nums.remove(session_index)
        sess_train = sess_nums
        sess_test = [session_index]
        
        print(f"Session分割信息：总session数={session_count}, 训练session={sess_train}, 测试session={sess_test}")
        logging.info(f"Session分割信息：总session数={session_count}, 训练session={sess_train}, 测试session={sess_test}")
        
        if isinstance(self.X, torch.Tensor):
            X_train = self.X[sub_index, sess_train]
            X_test = self.X[sub_index, sess_test]
            y_train = self.y[sub_index, sess_train]
            y_test = self.y[sub_index, sess_test]
        else:
            X_train = [[self.X[sub_index][x] for x in sess_train]]
            X_test = [[self.X[sub_index][x] for x in sess_test]]
            y_train = [[self.y[sub_index][x] for x in sess_train]]
            y_test = [[self.y[sub_index][x] for x in sess_test]]

        return X_train, y_train, X_test, y_test

    def split_loso(self, args):
        """
        根据受试者进行留一交叉验证划分:

        参数:

        args: 参数对象

        功能:

        根据当前受试者索引,将数据集分为训练和测试子集
        训练子集包含除指定受试者外的所有受试者数据
        测试子集包含指定受试者数据

        返回:

        X_train: 输入训练子集
        y_train: 输出训练子集
        X_test: 输入测试子集
        y_test: 输出测试子集
        """
        try:
            from metabci_integration.brainda_loso import generate_loso_indices
            sub_train, sub_test, meta = generate_loso_indices(
                subject_count=len(self.X),
                held_out_subject=args.cur_sub_index,
            )
            print(f"brainda LOSO划分完成: train={sub_train}, test={sub_test}")
            logging.info(f"brainda LOSO划分完成: {meta}")
        except Exception as e:
            print(f"brainda LOSO划分失败，回退到本地LOSO: {e}")
            logging.warning(f"brainda LOSO划分失败，回退到本地LOSO: {e}")
            sub_train = [i for i in range(len(self.X))]
            sub_train.remove(args.cur_sub_index)
            sub_test = [args.cur_sub_index]

        if isinstance(self.X, torch.Tensor):
            X_train = self.X[sub_train]
            X_test = self.X[sub_test]
            y_train = self.y[sub_train]
            y_test = self.y[sub_test]
        else:
            X_train = [self.X[x] for x in sub_train]
            y_train = [self.y[x] for x in sub_train]
            X_test = [self.X[x] for x in sub_test]
            y_test = [self.y[x] for x in sub_test]

        return X_train, y_train, X_test, y_test

    def split_k_fold(self, args):
        """
        根据受试者进行k折交叉验证划分:

        参数:

        args: 参数对象

        功能:

        根据当前受试者索引,将数据集分为训练和测试子集
        训练子集包含除指定受试者外的所有受试者数据
        测试子集包含指定受试者数据

        返回:

        X_train: 输入训练子集
        y_train: 输出训练子集
        X_test: 输入测试子集
        y_test: 输出测试子集
        """
        sub_num = len(self.X)
        one_fold_nums = int(sub_num / args.k_fold_nums)

        sub_train = [i for i in range(len(self.X))]
        sub_test = list(range(args.cur_sub_index, args.cur_sub_index + one_fold_nums))
        sub_train = [i for i in sub_train if i not in sub_test]

        if isinstance(self.X, torch.Tensor):
            X_train = self.X[sub_train]
            X_test = self.X[sub_test]
            y_train = self.y[sub_train]
            y_test = self.y[sub_test]
        else:
            X_train = [self.X[x] for x in sub_train]
            y_train = [self.y[x] for x in sub_train]
            X_test = [self.X[x] for x in sub_test]
            y_test = [self.y[x] for x in sub_test]

        return X_train, y_train, X_test, y_test

    def reshape_sample(self, X, y):
        r"""
        重塑样本形状:

        参数:

        X: 输入特征
        y: 输出目标

        功能:

        如果数据是张量,直接reshape成(index, channel, feature, band)形式
        如果数据是列表,需要对每个样本作滑动窗口操作使其张量化
        返回数据形状为(index, channel, feature, band)的张量

        返回:

        out_X: 重塑后输入特征
        out_y: 重塑后输出目标

        """

        # 如果输入的是tensor 那么数据是提前对齐的 直接reshape
        if isinstance(self.X, torch.Tensor):
            out_X = X.reshape(-1, X.shape[-3],
                              X.shape[-2], X.shape[-1])
            out_y = y.reshape(-1)

        # 如果不是对齐的那么输入的是列表，需要滑动窗口分割使其对齐
        elif self.args.spp:
            out_X, out_y = [], []
            for i in range(len(X)):
                for j in range(len(X[0])):
                    for k in range(len(X[0][0])):
                        out_X.append(X[i][j][k])
                        out_y.append(y[i][j][k].unsqueeze(0))

            out_y = torch.cat(out_y, 0)
        else:
            out_X, out_y = [], []
            for i in range(len(self.X)):
                for j in range(len(self.X[0])):
                    for k in range(len(self.X[0][0])):
                        temp_X = X[i][j][k].unsqueeze(0)
                        temp_y = y[i][j][k].unsqueeze(0)
                        temp_X, temp_y = self.window_slide(
                            self.args, temp_X, temp_y)
                        out_X.append(temp_X)
                        out_y.append(temp_y)
            out_X = torch.cat(out_X, 0)
            out_y = torch.cat(out_y, 0)
        return out_X, out_y

    def window_slide(self, args, X, y):
        r"""滑动窗口分割, 根据args里面的window_len和step参数进行切割

        对样本进行滑动窗口分割:

        参数:

        args: 参数对象,包含窗口长度和步长参数
        X: 输入特征
        y: 输出目标

        功能:

        根据窗口长度和步长参数对每个样本进行滑动窗口分割
        返回窗口化后的输入和输出组成的张量

        返回:

        X_slide: 滑动窗口分割后的输入特征张量
        y_slide: 滑动窗口分割后的输出目标张量

        """

        X_slide = []
        y_slide = []
        for i in range(len(y)):
            start = 0
            end = args.window_len
            X_temp = []
            y_temp = []
            while end < X.shape[-2]:
                X_temp.append(X[i, :, start:end, :].unsqueeze(0))
                y_temp.append(y[i].unsqueeze(0))
                start += args.step
                end += args.step
            X_temp.append(
                X[i, :, X.shape[-2] - args.window_len:, :].unsqueeze(0))
            y_temp.append(y[i].unsqueeze(0))
            X_slide.append(torch.cat(X_temp, dim=0))
            y_slide.append(torch.cat(y_temp, dim=0))
        X_slide = torch.cat(X_slide, dim=0)
        y_slide = torch.cat(y_slide, dim=0)
        return X_slide, y_slide

    def get_dataset_class(self):
        """
        获取数据集类:

        参数:

        无

        功能:

        根据配置中的数据集名称,从工厂字典中获取对应的数据集类

        返回:

        dataset工厂字典中对应的Dataset类,用于实例化后加载数据集
        """
        data_factory = {
            'seed': SEEDDataset,
            'seed_adj': SEEDAdjDataset,
            'seed_origin': SEEDDataset,
            'deap': DEAPDataset,
            'amigos': AMIGOSDataset,
            'seed_iv': SEEDIVDataset_spp,
            'seed_iv_adj': SEEDIVAdjDataset,
            'faced': FACEDataset,
        }
        return data_factory[self.args.dataset]

    def get_dataloader(self, is_train=True):
        r"""获取dataloader
        获取数据加载器:

        参数:

        is_train: 是否为训练集,默认为True

        功能:

        根据is_train变量切换训练/测试数据
        使用数据集类加载数据
        返回DataLoader加载器,包含batch处理及shuffle等操作

        返回:
        DataLoader对象,用于模型训练/测试数据的批量输入

        """

        if is_train:
            dataset = self.dataset(self.X_train, self.y_train)
        else:
            dataset = self.dataset(self.X_test, self.y_test)
        return DataLoader(dataset, num_workers=0, batch_size=int(self.args.batch_size), shuffle=True, drop_last=True)

    def get_label_dict(self, dataset='deap', label='valence'):
        label_dict = {
            'deap': {
                'valence': 0,
                'arousal': 1,
                'dominance': 2,
                'liking': 3
            }
        }

        return label_dict[dataset][label]





class SEEDDataset(Dataset):
    def __init__(self, X, y):
        '''
        SEEDDataset
        '''
        self.X = X.float()
        self.y = (y + 1 if y.min() < 0 else y).long()
        print((self.y == 0).sum(), (self.y == 1).sum(),
              (self.y == 2).sum(), len(self.y))

    def __len__(self):
        return len(self.y)

    def __getitem__(self, index):
        X = self.X[index]
        y = int(self.y[index])
        return X, y


class SEEDAdjDataset(Dataset):
    def __init__(self, X, y):
        '''
        SEEDDataset
        '''
        self.X = X
        self.y = y
        # print((self.y == 0).sum(), (self.y == 1).sum(),
        #       (self.y == 2).sum(), len(self.y))

    def __len__(self):
        return len(self.y)

    def __getitem__(self, index):
        X = self.X[index]
        data = X['data'].float()
        coh_adj = X['coh_adj'].float()
        pcc_adj = X['pcc_adj'].float()
        plv_adj = X['plv_adj'].float()
        nmi_adj = X['nmi_adj'].float()

        class_y = int(self.y[index, 0]+1)
        domain_y = int(self.y[index, 1])
        return (data, coh_adj, pcc_adj, plv_adj, nmi_adj), (class_y, domain_y)


class DEAPDataset(Dataset):
    def __init__(self, feature, label):
        '''

        '''

        self.feature = feature
        self.label = (label > 5)
        print((self.label == 0).sum(), (self.label == 1).sum(), len(self.label))

    def __len__(self):
        return len(self.label)

    def __getitem__(self, index):
        features = self.feature[index].float()
        label = self.label[index]
        label = int(label)
        return features, label


class AMIGOSDataset(Dataset):
    def __init__(self, feature, label):
        '''

        '''

        self.feature = feature
        self.label = label
        print((self.label == 0).sum(), (self.label == 1).sum(), len(self.label))

    def __len__(self):
        return len(self.label)

    def __getitem__(self, index):
        features = self.feature[index].float()
        label = self.label[index]
        label = int(label)
        return features, label


class SEEDIVDataset_spp(Dataset):
    def __init__(self, X, y):
        '''
        SEEDIVDataset_spp
        '''
        self.X = X
        self.y = y
        print((self.y == 0).sum(), (self.y == 1).sum(),
              (self.y == 2).sum(), (self.y == 3).sum(), len(self.y))
        logging.info(
            f'label0: {(self.y == 0).sum()}, label1: {(self.y == 1).sum()}, label2: {(self.y == 2).sum()}, label3: { (self.y == 3).sum()}, length: {len(self.y)}')

    def __len__(self):
        return len(self.y)

    def __getitem__(self, index):
        X = self.X[index].float()
        y = int(self.y[index])
        return X, y


class SEEDIVAdjDataset(Dataset):
    def __init__(self, X, y):
        '''
        SEEDIVAdjDataset
        '''
        self.X = X
        self.y = y
        # print((self.y == 0).sum(), (self.y == 1).sum(),
        #       (self.y == 2).sum(), len(self.y))

    def __len__(self):
        return len(self.y)

    def __getitem__(self, index):
        X = self.X[index]
        data = X['data'].float()
        coh_adj = X['coh_adj'].float()
        pcc_adj = X['pcc_adj'].float()
        plv_adj = X['plv_adj'].float()
        nmi_adj = X['nmi_adj'].float()

        class_y = int(self.y[index, 0])
        domain_y = int(self.y[index, 1])
        return (data, coh_adj, pcc_adj, plv_adj, nmi_adj), (class_y, domain_y)


class FACEDataset(Dataset):
    def __init__(self, X, y):
        '''
        FACEDataset
        '''
        self.X = X
        self.y = y
        print((self.y == 0).sum(),
              (self.y == 1).sum(),
              (self.y == 2).sum(),
              len(self.y))
        logging.info(
            f'label0: {(self.y == 0).sum()},label1: {(self.y == 1).sum()},label2: {(self.y == 2).sum()},length: {len(self.y)}')

    def __len__(self):
        return len(self.y)

    def __getitem__(self, index):
        X = self.X[index].float()
        y = int(self.y[index])
        return X, y




