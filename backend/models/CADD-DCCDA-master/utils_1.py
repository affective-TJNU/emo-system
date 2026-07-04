import torch
import torch.nn as nn
import copy
from torch.utils.data import Dataset
import numpy as np
from sklearn.model_selection import train_test_split

def load_data(args):
    if args.dataset == 'SEED':
        if args.feature == 'de':
            data = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/SEED/data_label/DE.pt')  # (15, 45, 1, 62, 265, 5)
            # data = torch.load('/home/bianning/Code/config/SEED/clip/data_slide.pt') # (15, 3, 15, 4/5, 1, 62, 60, 5) list
        elif args.dataset == 'psd':
            data = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/SEED/data_label/psd.pt') # (15, 45, 1, 62, 265, 5)
        elif args.dataset == 'dasm':
            data = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/SEED/data_label/dasm.pt')# (15, 45, 1, 27, 265, 5)
        elif args.dataset == 'rasm':
            data = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/SEED/data_label/rasm.pt')# (15, 45, 1, 62, 265, 5)
        elif args.dataset == 'asm':
            data = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/SEED/data_label/asm.pt') # (15, 45, 1, 54, 265, 5)
        else:
            data = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/SEED/data_label/dcau.pt')# (15, 45, 1, 23, 265, 5)
        label = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/SEED/data_label/label.pt')  # (15, 45, 1)
        # label = torch.load('/home/bianning/Code/config/SEED/clip/label_slide.pt')   # (15, 3, 15, 4/5, 1)
    
    elif args.dataset == 'DEAP':
        if args.feature == 'de':
            # data = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/de_data_time_step_16.pt')    # (32, 40, 1, 32, 465, 5)
            # data = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/de_data_time_step_32.pt')    # (32, 40, 1, 32, 233, 5)
            # data = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/de_data_time_step_128.pt')   # (32, 40, 1, 32, 59, 5)
            data = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/DEAP/clip_data.pt')   # (32, 40, 1, 32, 63, 5)
            # data = torch.load('/home/bianning/Code/config/DEAP/clip_data.pt')   # (32, 40, 7, 32, 63, 5)
        else:
            # data = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/psd_data_time_step_16.pt')    # (32, 40, 1, 32, 465, 5)
            # data = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/psd_data_time_step_32.pt')    # (32, 40, 1, 32, 233, 5)
            # data = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/psd_data_time_step_128.pt')   # (32, 40, 1, 32, 59, 5)
            data = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/DEAP/de_norm_data.pt')  # (32, 40, 1, 32, 63, 5)
            # data = torch.load('/home/bianning/Code/config/DEAP/remove_11_26/de_norm_data.pt')  # (30, 40, 1, 32, 63, 5)
            # data = torch.load('/home/bianning/Code/config/DEAP/remove_5_subjects/de_norm_data.pt')  # (27, 40, 1, 32, 63, 5)
        if args.label_type == 'arousal':
            label = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/DEAP/label_16_arousal.pt') # (32, 40, 1)
            # label = torch.load('/home/bianning/Code/config/DEAP/clip_arousal.pt') # (32, 40, 7)
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/label_32_arousal.pt')
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/label_128_arousal.pt')
            # label = torch.load('/home/bianning/Code/config/DEAP/STFT_result/label_arousal.pt')  # (32, 40, 1)
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_11_26/label_16_arousal.pt')  # (30, 40, 1)
        elif args.label_type == 'valence':
            label = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/DEAP/label_16_valence.pt') # (32, 40, 1)
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/label_32_valence.pt')
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/label_128_valence.pt')
            # label = torch.load('/home/bianning/Code/config/DEAP/STFT_result/label_valence.pt')  # (32, 40, 1)
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_11_26/label_16_valence.pt')  # (30, 40, 1)
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_5_subjects/label_16_valence.pt') # (27, 40, 1)
            # label = torch.load('/home/bianning/Code/config/DEAP/clip_valence.pt') # (32, 40, 7)
        elif args.label_type == 'dominance':
            label = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/DEAP/label_16_dominance.pt')   # (32, 40, 1)
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/label_32_dominance.pt')
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/label_128_dominance.pt')
        else:
            label = torch.load('/mnt/external_ssd/yanyajing2024/Code/数据集/DEAP/label_16_liking.pt')  # (32, 40, 1)
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/label_32_liking.pt')
            # label = torch.load('/home/bianning/Code/config/DEAP/remove_data_label/label_128_liking.pt')
    
    elif args.dataset == 'DREAMER':
        if args.feature == 'de':
            data = torch.load('/home/bianning/Code/config/DREAMER/de_data.pt') # (23, 64, 1, 14, 261, 5)
        else:
            data = torch.load('/home/bianning/Code/config/DREAMER/psd_data.pt')# (23, 64, 1, 14, 261, 5)
        if args.label_type == 'arousal':
            label = torch.load('/home/bianning/Code/config/DREAMER/2_label_arousal.pt') # (23, 64, 1)
        elif args.label_type == 'valence':
            label = torch.load('/home/bianning/Code/config/DREAMER/2_label_valence.pt') # (23, 64, 1)
        else:
            label = torch.load('/home/bianning/Code/config/DREAMER/2_label_dominance.pt')   # (23, 64, 1)

    else:
        # data = torch.load('/home/bianning/Code/config/AMIGOS/psd_data_non_norm.pt')
        # data = torch.load('/home/bianning/Code/config/AMIGOS/psd_data_others.pt')   # 65归一化
        data = torch.load('/home/bianning/Code/config/AMIGOS/psd_data.pt')  # (28, 340, 1, 14, 20, 5)
        # data = torch.load('/home/bianning/Code/config/AMIGOS/psd_data_others_balence.pt')
        if args.label_type == 'arousal':
            label = torch.load('/home/bianning/Code/config/AMIGOS/zero_arousal_label.pt')   # (28, 340, 1)
            # label = torch.load('/home/bianning/Code/config/AMIGOS/zero_arousal_label_balence.pt')
        else:
            label = torch.load('/home/bianning/Code/config/AMIGOS/zero_valence_label.pt')

    return data, label

def load_data_cross_dataset(args):
    if args.dataset == 'SEED_DEAP':
        source_data = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/data_SEED_slide_14_9_1.pt')    # (15, 990, 1, 14, 9, 5)
        target_data = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/data_DEAP_slide_14_9_1.pt')    # (32, 280, 1, 14, 9, 5)
        source_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_SEED_slide_9_1.pt')     # (15, 990, 1)
        if args.label_type == 'valence':
            target_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_DEAP_slide_valence_9_1.pt') # (32, 280, 1)
        else:
            target_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_DEAP_slide_arousal_9_1.pt') # (32, 280, 1)
    
    elif args.dataset == 'DEAP_SEED':
        target_data = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/data_SEED_slide_14_9_1.pt')    # (15, 990, 1, 14, 9, 5)
        source_data = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/data_DEAP_slide_14_9_1.pt')    # (32, 280, 1, 14, 9, 5)
        target_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_SEED_slide_9_1.pt')     # (15, 990, 1)
        if args.label_type == 'valence':
            source_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_DEAP_slide_valence_9_1.pt') # (32, 280, 1)
        else:
            source_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_DEAP_slide_arousal_9_1.pt') # (32, 280, 1)
    # if args.dataset == 'SEED_DEAP':
    #     source_data = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/data_SEED_slide_14.pt')    # (15, 7710, 1, 14, 9, 5)
    #     target_data = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/data_DEAP_slide_14.pt')    # (32, 2200, 1, 32, 9, 5)
    #     source_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_SEED_slide.pt')     # (15, 7710, 1)
    #     if args.label_type == 'valence':
    #         target_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_DEAP_slide_valence.pt') # (32, 2200, 1)
    #     else:
    #         target_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_DEAP_slide_arousal.pt') # (32, 2200, 1)
    
    # elif args.dataset == 'DEAP_SEED':
    #     target_data = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/data_SEED_slide_14.pt')    # (15, 7710, 1, 14, 9, 5)
    #     source_data = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/data_DEAP_slide_14.pt')    # (32, 2200, 1, 32, 9, 5)
    #     target_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_SEED_slide.pt')     # (15, 7710, 1)
    #     if args.label_type == 'valence':
    #         source_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_DEAP_slide_valence.pt') # (32, 2200, 1)
    #     else:
    #         source_label = torch.load('/home/bianning/Code/CADD_DCCNN_1/cross_dataset/label_DEAP_slide_arousal.pt') # (32, 2200, 1)
    
    return source_data, source_label, target_data, target_label

def sum_loss_with_parameter(label_pred, label_true, dc_src_pred, dc_src_true, dc_tgt_pred, dc_tgt_true, args):
    lc_loss = nn.CrossEntropyLoss()(label_pred, label_true.squeeze().long())
    dc_src_loss = nn.CrossEntropyLoss()(dc_src_pred, dc_src_true.squeeze().long())
    dc_tgt_loss = nn.CrossEntropyLoss()(dc_tgt_pred, dc_tgt_true.squeeze().long())

    total_loss = lc_loss + args.loss_alpha * dc_src_loss + args.loss_beta * dc_tgt_loss

    return lc_loss, dc_src_loss, dc_tgt_loss, total_loss

def sum_loss_with_parameter_without_dd(label_pred, label_true, dc_src_pred, dc_src_true, dc_tgt_pred, dc_tgt_true, args):
    lc_loss = nn.CrossEntropyLoss()(label_pred, label_true.squeeze().long())
    dc_src_loss = nn.CrossEntropyLoss()(dc_src_pred, dc_src_true.squeeze().long())
    dc_tgt_loss = nn.CrossEntropyLoss()(dc_tgt_pred, dc_tgt_true.squeeze().long())

    total_loss = lc_loss

    return lc_loss, dc_src_loss, dc_tgt_loss, total_loss

def data_loaders(data, label, args):
    data_loader = torch.utils.data.DataLoader(dataset=CustomDataset(data, label), 
                                              batch_size=args.batch_size, 
                                              shuffle=True, 
                                              drop_last=True)
    
    return data_loader

def valid_data_loader(source_dataloader, target_dataloader, data, label, args):
    valid_data = []
    valid_label = []
    for i in range(int(len(source_dataloader) / len(target_dataloader)) + 1):
        valid_data.append(np.array(data))
        valid_label.append(np.array(label))
    valid_data = torch.Tensor(np.array(valid_data).reshape(-1, 1, args.channels, args.length, args.bands))
    valid_label = torch.Tensor(np.array(valid_label).reshape(-1, 1))
    valid_dataloader = torch.utils.data.DataLoader(dataset=CustomDataset(valid_data, valid_label), 
                                            batch_size=args.batch_size, 
                                            shuffle=True, 
                                            drop_last=True)
    
    return valid_dataloader

def Leave_one_subject_out(subject_id, args):
    data, label = load_data(args=args)
    train_idex = list(range(args.subjects))
    del train_idex[subject_id]
    test_idex = subject_id
    source_data, source_label = copy.deepcopy(data[train_idex]), copy.deepcopy(label[train_idex])
    target_data, target_label = copy.deepcopy(data[test_idex]), copy.deepcopy(label[test_idex])
    source_data = source_data.reshape(-1, source_data.shape[2], source_data.shape[3], source_data.shape[4], source_data.shape[5])
    source_label = source_label.reshape(-1, source_label.shape[2])
    source_iters = data_loaders(source_data, source_label, args)
    target_iters = data_loaders(target_data, target_label, args)
    valid_iters = valid_data_loader(source_iters, target_iters, target_data, target_label, args)
    
    return source_iters, target_iters, valid_iters

def Leave_one_session_out(subject_id, session_id, args):
    data, label = load_data(args=args)
    data = data.reshape(data.shape[0], 3, 15, data.shape[2], data.shape[3], data.shape[4], data.shape[5])   # (15, 3, 15, 1, 62, 265, 5)
    label = label.reshape(label.shape[0], 3, 15, label.shape[2])    # (15, 3, 15, 1)
    train_idex = list(range(3))
    del train_idex[session_id]
    test_idex = session_id
    source_data = data[subject_id, train_idex, :, :, :, :, :].reshape(-1, data.shape[3], data.shape[4], data.shape[5], data.shape[6])
    source_label = label[subject_id, train_idex, :, :].reshape(-1, label.shape[3])   # (450, 1)
    target_data = data[subject_id, test_idex, :, :, :, :, :].reshape(-1, data.shape[3], data.shape[4], data.shape[5], data.shape[6])
    target_label = label[subject_id, test_idex, :, :].reshape(-1, label.shape[3])   # (225, 1)
    source_iters = data_loaders(source_data, source_label, args)
    target_iters = data_loaders(target_data, target_label, args)
    valid_iters = valid_data_loader(source_iters, target_iters, target_data, target_label, args)
    
    return source_iters, target_iters, valid_iters

def Leave_one_clip_out(clip_id, args, subject_id):
    data, label = load_data(args=args)
    train_idex = list(range(args.trials))
    del train_idex[clip_id]
    test_idex = clip_id
    source_data = data[subject_id, train_idex, :, :, :, :].reshape(-1, 1, data.shape[3], data.shape[4], data.shape[5])
    source_label = label[subject_id, train_idex, :].reshape(-1, 1)   # (1248, 1)
    target_data = data[subject_id, test_idex, :, :, :, :].reshape(-1, 1, data.shape[3], data.shape[4], data.shape[5])
    target_label = label[subject_id, test_idex, :].reshape(-1, 1)   # (32, 1)
    source_iters = data_loaders(source_data, source_label, args)
    target_iters = data_loaders(target_data, target_label, args)
    valid_iters = valid_data_loader(source_iters, target_iters, target_data, target_label, args)
    
    return source_iters, target_iters, valid_iters

def subject_split_data(args):
    subject_num_list=list(range(args.subjects))
    subject_source,subject_target=train_test_split(subject_num_list,test_size=0.1)#将受试者编号按 9:1 的比例分为训练集,10% 的受试者作为测试集，剩余的 90% 作为训练集。

    data, label = load_data(args=args)
    source_data, source_label, target_data, target_label = [], [], [], []
    source_data = data[subject_source].view(-1, data.shape[2], data.shape[3], data.shape[4], data.shape[5])
    source_label = label[subject_source].view(-1, label.shape[2])
    target_data = data[subject_target].view(-1, data.shape[2], data.shape[3], data.shape[4], data.shape[5])
    target_label = label[subject_target].view(-1, label.shape[2])
    source_iters = data_loaders(source_data, source_label, args)
    target_iters = data_loaders(target_data, target_label, args)
    valid_iters = valid_data_loader(source_iters, target_iters, target_data, target_label, args)

    return source_iters, target_iters, valid_iters

def trial_split_data(subject_id, args):
    # # (15, 3, 15, 4/5, 1, 62, 60, 5)
    # data, label = load_data(args=args)
    # data_source = []
    # data_target = []
    # label_source = []
    # label_target = []
    # for i in range(3):
    #     mid_data_source = []
    #     mid_data_target = []
    #     mid_label_source = []
    #     mid_label_target = []
    #     for j in range(9):
    #         mid_data_source.append(data[subject_id][i][j])
    #         mid_label_source.append(label[subject_id][i][j])
    #     mid_data_source = torch.cat(mid_data_source, dim=0)
    #     mid_label_source = torch.cat(mid_label_source, dim=0)
    #     data_source.append(mid_data_source)
    #     label_source.append(mid_label_source)
    #     for j in range(9, 15):
    #         mid_data_target.append(data[subject_id][i][j])
    #         mid_label_target.append(label[subject_id][i][j])
    #     mid_data_target = torch.cat(mid_data_target, dim=0)
    #     mid_label_target = torch.cat(mid_label_target, dim=0)
    #     data_target.append(mid_data_target)
    #     label_target.append(mid_label_target)
    # data_source = torch.cat(data_source, dim=0)
    # label_source = torch.cat(label_source, dim=0)
    # data_target = torch.cat(data_target, dim=0)
    # label_target = torch.cat(label_target, dim=0)
    # source_iters = data_loaders(data_source, label_source, args)
    # target_iters = data_loaders(data_target, label_target, args)
    # valid_iters = valid_data_loader(source_iters, target_iters, data_target, label_target, args)

    # (15, 45, 1, 62, 265, 5)
    data, label = load_data(args=args)
    data = data.reshape(data.shape[0], 3, -1, data.shape[2], data.shape[3], data.shape[4], data.shape[5])   # (15, 3, 15, 29, 62, 9, 5)
    label = label.reshape(label.shape[0], 3, -1, label.shape[2])    # (15, 3, 15, 29)
    # trial_source = list(range(12))                  # (0, 12)    13
    # trial_target = list(range(12, 15))              # (13, 14)   2
    trial_source = list(range(int(args.trials / 3.0 * 0.6)))                            # (0, 8)    9
    trial_target = list(range(int(args.trials / 3.0 * 0.6), int(args.trials / 3.0)))    # (9, 14)   6  按照试验划分比例（60% 训练，40% 测试）划分 trial_source 和 trial_target
    source_data = data[subject_id, :, trial_source, :, :, :, :].view(-1, 1, data.shape[4], data.shape[5], data.shape[6])
    source_label = label[subject_id, :, trial_source, :].view(-1, 1)
    target_data = data[subject_id, :, trial_target, :, :, :, :].view(-1, 1, data.shape[4], data.shape[5], data.shape[6])
    target_label = label[subject_id, :, trial_target, :].view(-1, 1)
    source_iters = data_loaders(source_data, source_label, args)
    target_iters = data_loaders(target_data, target_label, args)
    valid_iters = valid_data_loader(source_iters, target_iters, target_data, target_label, args)

    return source_iters, target_iters, valid_iters

def cross_dataset(args):
    source_data, source_label, target_data, target_label = load_data_cross_dataset(args)
    source_data = source_data.reshape(-1, source_data.shape[2], source_data.shape[3], source_data.shape[4], source_data.shape[5])
    source_label = source_label.reshape(-1, source_label.shape[2])
    target_data = target_data.reshape(-1, target_data.shape[2], target_data.shape[3], target_data.shape[4], target_data.shape[5])
    target_label = target_label.reshape(-1, target_label.shape[2])
    # data = target_data[0].reshape(-1, target_data.shape[1], target_data.shape[2], target_data.shape[3], target_data.shape[4])
    # label = target_label[0].reshape(-1, target_label.shape[1])
    source_iters = data_loaders(source_data, source_label, args)
    target_iters = data_loaders(target_data, target_label, args)
    # valid_iters = valid_data_loader(source_iters, data, data, label, args)
    valid_iters = valid_data_loader(source_iters, target_iters, target_data, target_label, args)
    return source_iters, target_iters, valid_iters

class CustomDataset(Dataset):
    # initialization: data and label
    def __init__(self, Data, Label):
        print('dataset:',Data.shape)
        # time.sleep(10000)
        self.Data = Data
        self.Label = Label.numpy()
    # get the size of data
    def __len__(self):
        return len(self.Data)
    # get the data and label
    def __getitem__(self, index):
        data = torch.Tensor((self.Data[index]).type(torch.float))
        label = self.Label[index]
        for i in range(label.shape[0]):
            label[i] = int(label[i])
        label = torch.LongTensor(label)
        return data, label