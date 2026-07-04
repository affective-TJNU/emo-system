import argparse
import csv
import time
import torch
import numpy as np
import random
import torch.optim as optim
from sklearn.metrics import f1_score
from models_1 import *
from utils_1 import *

def arg_parse():
    '''
    argument parser
    '''
    parser = argparse.ArgumentParser(description='Cross-attention Neural Network Based on Dilation and Casual CNN')
    parser.add_argument('--models', type=str, help='name of models')
    parser.add_argument('--UI_UD', type=str, help='User independent or User dependent')
    parser.add_argument('--dataset', type=str, help='dataset')
    parser.add_argument('--feature', type=str, help='feature of SEED')
    parser.add_argument('--label_type', type=str, help='label type of DEAP')
    parser.add_argument('--seed', type=int, help='manual seed')
    parser.add_argument('--data_split', type=str, help='cross_subject or cross_session')
    parser.add_argument('--epoch', type=int, help='number of epoch')
    parser.add_argument('--batch_size', type=int, help='number of batch_size')
    parser.add_argument('--subjects', type=int, help='number of subjects')
    parser.add_argument('--target_subjects', type=int, help='number of target dataset subjects')
    parser.add_argument('--trials', type=int, help='number of trials')
    parser.add_argument('--target_trials', type=int, help='number of target dataset trials')
    parser.add_argument('--channels', type=int, help='number of channels')
    parser.add_argument('--length', type=int, help='length of EEG')
    parser.add_argument('--bands', type=int, help='number of bands')
    parser.add_argument('--nclass', type=int, help='number of classification')
    parser.add_argument('--domain_class', type=int, help='number of domain')
    parser.add_argument('--gpu', type=int, help='number of gpu')
    parser.add_argument('--lr', type=float, help='learning_rate')
    parser.add_argument('--grl_alpha', type=float, help='parameter of GRL layer')
    parser.add_argument('--conv1_out_dim', type=int, help='out_dim of Conv_1 layer')
    parser.add_argument('--conv1_H', type=int, help='H kernal_size of Conv_1 layer')
    parser.add_argument('--conv1_W', type=int, help='W kernal_size of Conv_1 layer')
    parser.add_argument('--conv2_out_dim', type=int, help='out_dim of Conv_2 layer')
    
    parser.add_argument('--conv2_H', type=int, help='H kernal_size of Conv_1 layer')
    parser.add_argument('--conv2_W', type=int, help='W kernal_size of Conv_1 layer')
    parser.add_argument('--conv3_out_dim', type=int, help='out_dim of Conv_3 layer')
    parser.add_argument('--conv3_H', type=int, help='H kernal_size of Conv_1 layer')
    parser.add_argument('--conv3_W', type=int, help='W kernal_size of Conv_1 layer')
    parser.add_argument('--loss_alpha', type=float, help='source data loss parameter of domain classifier')
    parser.add_argument('--loss_beta', type=float, help='target data loss parameter of domain classifier')
    parser.add_argument('--fc1_dim', type=int, help='FC_1 layer out dim')
    parser.add_argument('--fc2_dim', type=int, help='FC_2 layer out dim')
    parser.add_argument('--log_interval', type=int, help='number of interval')

    parser.set_defaults(models = 'CADD_DCCNN', 
                        UI_UD = 'UI', 
                        dataset = 'DEAP',
                        feature = 'de', 
                        label_type = 'normal', 
                        seed = 1, 
                        data_split = 'LOSO_subject', 
                        epoch = 10,
                        batch_size = 5,
                        subjects = 32,
                        target_subjects = 32, 
                        trials = 40, 
                        target_trials = 32, 
                        channels = 32, 
                        length = 265, 
                        bands = 5, 
                        nclass = 3,
                        domain_class = 2,
                        gpu = 0,
                        lr = 1e-4,
                        grl_alpha = 1, 
                        conv1_out_dim = 72,
                        conv1_H = 1, 
                        conv1_W = 8, 
                        conv2_out_dim = 48,
                        conv2_H = 1, 
                        conv2_W = 5, 
                        conv3_out_dim = 24,
                        conv3_H = 1, 
                        conv3_W = 3, 
                        loss_alpha = 1,
                        loss_beta = 1,
                        fc1_dim = 1024,
                        fc2_dim = 150, 
                        log_interval = 10)
    
    return parser.parse_args()

def setup_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True

def setup_device(gpu=0):
    # 设置GPU
    if torch.cuda.is_available():
        device = 'cuda:{}'.format(gpu)
    else:
        device = 'cpu'
    return device

def get_time(t1, t2):
    run_time = round(t2-t1)
    # 计算时分秒
    hour = run_time//3600
    minute = (run_time-3600*hour)//60
    second = run_time-3600*hour-60*minute
    # 输出
    print(f'该程序运行时间：{hour}小时{minute}分钟{second}秒')

def log(args, train_loss, train_acc, test_loss, test_acc, test_std, path):
    f = open(path, 'a', encoding="utf-8")
    csv_writer = csv.writer(f)


    csv_writer.writerow([args.models, args.UI_UD, args.dataset, args.subjects, args.feature, args.label_type, args.nclass, args.epoch, args.batch_size, args.lr, args.seed, 
                         train_loss, train_acc, test_loss, test_acc, test_std, 
                         args.conv1_out_dim, args.conv2_out_dim, args.conv3_out_dim, 
                         args.loss_alpha, args.loss_beta, args.fc1_dim, args.fc2_dim])
    f.close()

def train_every_epoch(model, source_iters, valid_iters, device, optimizer, args):
    epoch_loss_array = []
    true_sample = 0
    num_iter = 1
    src_tsne = []
    tgt_tsne = []
    for (source_data, source_label), (target_data, _) in zip(source_iters, valid_iters):
        dlabel_src = torch.zeros(args.batch_size, 1).to(device)
        dlabel_tgt = torch.ones(args.batch_size, 1).to(device)
        source_data, source_label = source_data.to(device), source_label.to(device)
        target_data = target_data.to(device)
        src_label_pred, src_domain_pred, _, src_tsne_d, data_att, _, _ = model(source_data)
        _, tgt_domain_pred, _, tgt_tsne_d, _, _, _ = model(target_data)
        src_tsne.append(src_tsne_d)
        tgt_tsne.append(tgt_tsne_d)
        lc_loss, dc_src_loss, dc_tgt_loss, loss = model.loss(src_label_pred, source_label, 
                                                             src_domain_pred, dlabel_src, 
                                                             tgt_domain_pred, dlabel_tgt)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        epoch_loss_array.append(loss.item())
        pred = src_label_pred.data.max(1, keepdim=True)[1]
        iter_true_sample = pred.eq(source_label.data.view_as(pred)).cpu().sum().item()
        true_sample += iter_true_sample
        print('Train: iter: {}\tLoss: {:.6f}\tlc_loss: {:.6f}\tdc_src_loss {:.6f}\tdc_tgt_loss: {:.6f}'.format(
              num_iter, loss.item(), lc_loss.item(), dc_src_loss.item(), dc_tgt_loss.item()))
        num_iter += 1
    train_acc = true_sample / len(source_iters) / args.batch_size

    return train_acc, epoch_loss_array, src_tsne, tgt_tsne, data_att

def train(model, source_iters, target_iters, valid_iters, device, optimizer, subject_id, args, with_valid):
    train_loss_array = []
    train_acc_array = []
    test_acc_array = []
    test_loss_array = []
    pred_array = []
    label_array = []
    best_test_acc = 0.
    for epoch in range(args.epoch):
        model.train()
        train_acc, train_loss, src_tsne, tgt_tsne, data_att = train_every_epoch(model, source_iters, valid_iters, device, optimizer, args)
        train_acc_array.append(train_acc)
        train_loss_array.append(train_loss)
        if with_valid:
            test_loss, test_acc, pred, label, tsne_test, fc_2, fc_3 = test(model, target_iters, device, args)
            test_acc_array.append(test_acc)
            test_loss_array.append(test_loss)
            if test_acc > best_test_acc:
                best_test_acc = test_acc
                best_test_epoch = epoch
                best_test_loss = test_loss
                best_test_tsne = tsne_test
                best_src_tsne = src_tsne
                best_tgt_tsne = tgt_tsne
                best_data_att = data_att
                best_fc_2 = fc_2
                best_fc_3 = fc_3
                best_pred = pred
                best_label = label
        print('Subject_id={}, Epoch={}, train_loss={:.4f}, train_acc={:.2f}%, test_acc={:.2f}%, test_loss={:.2f}'.format(
              subject_id, epoch+1, np.mean(train_loss), train_acc*100, test_acc*100, test_loss))
    pred_array = np.array(best_pred)
    label_array = np.array(best_label)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/label_result/' + args.dataset + '_pred_' + str(subject_id+1) + '.npy', pred_array)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/label_result/' + args.dataset + '_label_' + str(subject_id+1) + '.npy', label_array)
    print('best test acc:{:.2f}%,best test epoch:{},std:{:.4f}'.format(
          best_test_acc*100, best_test_epoch, float(torch.FloatTensor(test_acc_array).std())))
    #添加
    print(best_test_tsne)
    best_test_tsne = np.array(best_test_tsne)
    best_src_tsne = np.array(best_src_tsne)
    best_tgt_tsne = np.array(best_tgt_tsne)
    best_fc_2 = np.array(best_fc_2)
    best_fc_3 = np.array(best_fc_3)
    best_data_att = best_data_att.cpu().detach().numpy()



    np.save('/mnt/external_ssd/yanyajing2024/CADD_DCCNN_1/result/tsne_result/tsne/' + args.dataset + '_' + args.data_split + '_' + str(subject_id+1) + '.npy', best_test_tsne)
    np.save('/mnt/external_ssd/yanyajing2024/CADD_DCCNN_1/result/tsne_result/src_tsne/' + args.dataset + '_' + args.data_split + '_src_' + str(subject_id+1) + '.npy', best_src_tsne)
    np.save('/mnt/external_ssd/yanyajing2024/CADD_DCCNN_1/result/tsne_result/tgt_tsne/' + args.dataset + '_' + args.data_split + '_tgt_' + str(subject_id+1) + '.npy', best_tgt_tsne)
    np.save('/mnt/external_ssd/yanyajing2024/CADD_DCCNN_1/result/tsne_result/att/' + args.dataset + '_' + args.data_split + '_att_' + str(subject_id+1) + '.npy', best_data_att)
    np.save('/mnt/external_ssd/yanyajing2024/CADD_DCCNN_1/result/tsne_result/fc_2/' + args.dataset + '_' + args.data_split + '_fc_2_' + str(subject_id+1) + '.npy', best_fc_2)
    np.save('/mnt/external_ssd/yanyajing2024/CADD_DCCNN_1/result/tsne_result/fc_3/' + args.dataset + '_' + args.data_split + '_fc_3_' + str(subject_id+1) + '.npy', best_fc_3)


    # np.save('/home/bianning/Code/CADD_DCCNN_1/result/tsne_result/' + args.dataset + '_' + args.data_split + '_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_test_tsne)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/result/tsne_result/' + args.dataset + '_' + args.data_split + '_src_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_src_tsne)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/result/tsne_result/' + args.dataset + '_' + args.data_split + '_tgt_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_tgt_tsne)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/result/tsne_result/' + args.dataset + '_' + args.data_split + '_att_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_data_att)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/result/tsne_result/' + args.dataset + '_' + args.data_split + '_fc_2_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_fc_2)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/result/tsne_result/' + args.dataset + '_' + args.data_split + '_fc_3_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_fc_3)

    # np.save('/home/bianning/Code/CADD_DCCNN_1/tsne_result/' + args.dataset + '_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_test_tsne)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/tsne_result/' + args.dataset + '_src_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_src_tsne)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/tsne_result/' + args.dataset + '_tgt_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_tgt_tsne)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/tsne_result/' + args.dataset + '_att_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_data_att)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/tsne_result/' + args.dataset + '_fc_2_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_fc_2)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/tsne_result/' + args.dataset + '_fc_3_' + str(subject_id+1) + '_' + str(best_test_epoch+1) + '.npy', best_fc_3)

    return np.mean(train_loss_array), np.mean(train_acc_array)*100, best_test_acc*100, best_test_loss, float(torch.FloatTensor(test_acc_array*100).std()), pred_array, label_array

def test(model, target_iters, device, args):
    test_loss_array = []
    pred_array = []
    label_array = []
    f1_score_array = []
    tsne_test = []
    fc_2 = []
    fc_3 = []
    true_sample = 0
    model.eval()
    with torch.no_grad():
        for data, label in target_iters:
            data = data.to(device)
            label = label.to(device)
            label_pred, _, tsne, _, _, fc_2_l, fc_3_l = model(data)
            tsne_test.append(tsne)
            fc_2.append(fc_2_l)
            fc_3.append(fc_3_l)
            _, _, _, loss = model.loss(label_pred, label)
            test_loss_array.append(loss.item())
            pred = label_pred.data.max(1, keepdim=True)[1]
            pred_array.append(np.array(pred.cpu()))
            label_array.append(np.array((label.data.view_as(pred)).cpu()))
            iter_true_sample = pred.eq(label.data.view_as(pred)).cpu().sum().item()
            true_sample += iter_true_sample
        acc = true_sample / len(target_iters) / args.batch_size
    
    return np.mean(test_loss_array), acc, pred_array, label_array, tsne_test, fc_2, fc_3

def train_every_epoch_CA_DCCNN(model, source_iters, valid_iters, device, optimizer, args):
    epoch_loss_array = []
    true_sample = 0
    num_iter = 1
    for (source_data, source_label), (target_data, _) in zip(source_iters, valid_iters):
        source_data, source_label = source_data.to(device), source_label.to(device)
        target_data = target_data.to(device)
        src_label_pred, _, _, _, data_att, _, _ = model(source_data)
        _, _, _, _, _, _, _ = model(target_data)
        lc_loss, _, _, loss = model.loss(src_label_pred, source_label)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        epoch_loss_array.append(loss.item())
        pred = src_label_pred.data.max(1, keepdim=True)[1]
        iter_true_sample = pred.eq(source_label.data.view_as(pred)).cpu().sum().item()
        true_sample += iter_true_sample
        print('Train: iter: {}\tLoss: {:.6f}\tlc_loss: {:.6f}\tdc_src_loss {:.6f}\tdc_tgt_loss: {:.6f}'.format(
              num_iter, loss.item(), lc_loss.item(), 0, 0))
        num_iter += 1
    train_acc = true_sample / len(source_iters) / args.batch_size

    return train_acc, epoch_loss_array, data_att

def train_CA_DCCNN(model, source_iters, target_iters, valid_iters, device, optimizer, subject_id, args, with_valid):
    train_loss_array = []
    train_acc_array = []
    test_acc_array = []
    test_loss_array = []
    best_test_acc = 0.
    for epoch in range(args.epoch):
        model.train()
        train_acc, train_loss, data_att = train_every_epoch_CA_DCCNN(model, source_iters, valid_iters, device, optimizer, args)
        train_acc_array.append(train_acc)
        train_loss_array.append(train_loss)
        if with_valid:
            test_loss, test_acc, pred, label_array, tsne_test, fc_2, fc_3 = test(model, target_iters, device, args)
            test_acc_array.append(test_acc)
            test_loss_array.append(test_loss)
            if test_acc > best_test_acc:
                best_test_acc = test_acc
                best_test_epoch = epoch
                best_test_loss = test_loss
                best_data_att = data_att
                best_fc_2 = fc_2
                best_fc_3 = fc_3
                best_pred = pred
                best_label = label_array
        print('Subject_id={}, Epoch={}, train_loss={:.4f}, train_acc={:.2f}%, test_acc={:.2f}%, test_loss={:.2f}'.format(
              subject_id, epoch+1, np.mean(train_loss), train_acc*100, test_acc*100, test_loss))
    pred_array = np.array(best_pred)
    label_array = np.array(best_label)
    print('best test acc:{:.2f}%,best test epoch:{},std:{:.4f}'.format(
          best_test_acc*100, best_test_epoch, float(torch.FloatTensor(test_acc_array).std())))
    best_fc_2 = np.array(best_fc_2)
    best_fc_3 = np.array(best_fc_3)
    best_data_att = best_data_att.cpu().detach().numpy()

    return np.mean(train_loss_array), np.mean(train_acc_array)*100, best_test_acc*100, best_test_loss, float(torch.FloatTensor(test_acc_array*100).std()), pred_array, label_array

def model_choose(args, device):
    if args.models == 'DANN':
        model = DANN(args, device)
    elif args.models == 'DANN_CA':
        model = DANN_CA(args, device)
    elif args.models == 'DANN_DCCNN':
        model = DANN_DCCNN(args, device)
    elif args.models == 'Model_Pool':
        model = Model_Pool(args, device)
    elif args.models == 'Model_Band_Att':
        model = Model_1(args, device)
    elif args.models == 'CA_DCCNN':
        model = CA_DCCNN(args, device)
    else:
        model = Model(args, device)
    return model

def main():
    args = arg_parse()
    setup_seed(seed=args.seed)
    device = setup_device(args.gpu)
    print(args)
    train_loss_array = []
    train_acc_array = []
    test_loss_array = []
    test_acc_array = []
    pred_list = []
    label_list = []
    if args.data_split == 'subject_split':
        model = model_choose(args, device)
        model.to(device)
        print(model)
        optimizer = optim.Adam(model.parameters(), lr=args.lr)
        source_iters, target_iters, valid_iters = subject_split_data(args=args)
        subject_id = args.subjects
        train_loss_array, train_acc_array, test_acc_array, test_loss_array, _, pred, label = train(model, source_iters, target_iters, valid_iters, device, 
                                                                                                   optimizer, subject_id, args, with_valid=True)
        pred_list = pred
        label_list = label
        print('cross_subject: ', test_acc_array)
        std = float('nan')
        print('avg_acc: {}\tstd: {}'.format(np.mean(test_acc_array), std))
    elif args.data_split == 'trial_split':
        for subject_id in range(args.subjects):
            model = model_choose(args, device)
            model.to(device)
            print(model)
            optimizer = optim.Adam(model.parameters(), lr=args.lr)
            source_iters, target_iters, valid_iters = trial_split_data(subject_id=subject_id, args=args)                             
            train_loss, train_acc, test_acc, test_loss, _, pred, label = train(model, source_iters, target_iters, valid_iters, device, optimizer, 
                                                                subject_id, args, with_valid=True)
            train_loss_array.append(train_loss)
            train_acc_array.append(train_acc)
            test_acc_array.append(test_acc)
            test_loss_array.append(test_loss)
            pred_list.append(pred)
            label_list.append(label)
        # for subject_id in range(args.subjects):
        #     for session_id in range(3):
        #         model = model_choose(args, device)
        #         model.to(device)
        #         print(model)
        #         optimizer = optim.Adam(model.parameters(), lr=args.lr)
        #         source_iters, target_iters, valid_iters = trial_split_data(subject_id=subject_id, session_id = session_id, args=args)                             
        #         train_loss, train_acc, test_acc, test_loss, _, pred, label = train(model, source_iters, target_iters, valid_iters, device, optimizer, 
        #                                                             subject_id, args, with_valid=True)
        #         train_loss_array.append(train_loss)
        #         train_acc_array.append(train_acc)
        #         test_acc_array.append(test_acc)
        #         test_loss_array.append(test_loss)
        #         pred_list.append(pred)
        #         label_list.append(label)
        print('cross_trial: ', test_acc_array)
        std = float(torch.FloatTensor(test_acc_array).std())
        print('avg_acc: {}\tstd: {}'.format(np.mean(test_acc_array), std))
    elif args.data_split == 'LOSO_session':
        for subject_id in range(args.subjects):
            for session_id in range(3):
                model = model_choose(args, device)
                model.to(device)
                print(model)
                optimizer = optim.Adam(model.parameters(), lr=args.lr)
                source_iters, target_iters, valid_iters = Leave_one_session_out(subject_id, session_id, args)
                train_loss, train_acc, test_acc, test_loss, _, pred, label = train(model, source_iters, target_iters, valid_iters, device, optimizer, 
                                                                                subject_id, args, with_valid=True)
                train_loss_array.append(train_loss)
                train_acc_array.append(train_acc)
                test_acc_array.append(test_acc)
                test_loss_array.append(test_loss)
                pred_list.append(pred)
                label_list.append(label)
        print('cross_session: ', test_acc_array)
        std = float(torch.FloatTensor(test_acc_array).std())
        print('avg_acc: {}\tstd: {}'.format(np.mean(test_acc_array), std))
    elif args.data_split == 'cross_dataset':
        model = model_choose(args, device)
        model.to(device)
        print(model)
        optimizer = optim.Adam(model.parameters(), lr=args.lr)
        source_iters, target_iters, valid_iters = cross_dataset(args=args)
        subject_id = args.subjects
        train_loss_array, train_acc_array, test_acc_array, test_loss_array, _, pred, label = train(model, source_iters, target_iters, valid_iters, device, 
                                                                                                   optimizer, subject_id, args, with_valid=True)
        pred_list = pred
        label_list = label
        print('cross_dataset: ', test_acc_array)
        std = float('nan')
        print('avg_acc: {}\tstd: {}'.format(np.mean(test_acc_array), std))
    elif args.data_split == 'Leave_one_clip_out':
        for subject_id in range(args.subjects):
            for clip_id in range(args.trials):
                model = model_choose(args, device)
                model.to(device)
                print(model)
                optimizer = optim.Adam(model.parameters(), lr=args.lr)
                source_iters, target_iters, valid_iters = Leave_one_clip_out(clip_id=clip_id, args=args, subject_id=subject_id)
                train_loss, train_acc, test_acc, test_loss, _, pred, label = train(model, source_iters, target_iters, valid_iters, device, optimizer, 
                                                                                subject_id, args, with_valid=True)
                train_loss_array.append(train_loss)
                train_acc_array.append(train_acc)
                test_acc_array.append(test_acc)
                test_loss_array.append(test_loss)
                pred_list.append(pred)
                label_list.append(label)
        print('cross_clip: ', test_acc_array)
        std = float(torch.FloatTensor(test_acc_array).std())
        print('avg_acc: {}\tstd: {}'.format(np.mean(test_acc_array), std))
    elif args.data_split == 'LOSO_CA_DCCNN':
        for subject_id in range(args.subjects):
            model = CA_DCCNN(args, device)
            model.to(device)
            print(model)
            optimizer = optim.Adam(model.parameters(), lr=args.lr)
            source_iters, target_iters, valid_iters = Leave_one_subject_out(subject_id=subject_id, args=args)
            train_loss, train_acc, test_acc, test_loss, _, pred, label = train_CA_DCCNN(model, source_iters, target_iters, valid_iters, device, optimizer, 
                                                                               subject_id, args, with_valid=True)
            train_loss_array.append(train_loss)
            train_acc_array.append(train_acc)
            test_acc_array.append(test_acc)
            test_loss_array.append(test_loss)
            pred_list.append(pred)
            label_list.append(label)
        print('cross_subject: ', test_acc_array)
        std = float(torch.FloatTensor(test_acc_array).std())
        print('avg_acc: {}\tstd: {}'.format(np.mean(test_acc_array), std))
    else:
        for subject_id in range(args.subjects):
            model = model_choose(args, device)
            model.to(device)
            print(model)
            optimizer = optim.Adam(model.parameters(), lr=args.lr)
            source_iters, target_iters, valid_iters = Leave_one_subject_out(subject_id=subject_id, args=args)
            train_loss, train_acc, test_acc, test_loss, _, pred, label = train(model, source_iters, target_iters, valid_iters, device, optimizer, 
                                                                               subject_id, args, with_valid=True)
            train_loss_array.append(train_loss)
            train_acc_array.append(train_acc)
            test_acc_array.append(test_acc)
            test_loss_array.append(test_loss)
            pred_list.append(pred)
            label_list.append(label)
        print('cross_subject: ', test_acc_array)
        std = float(torch.FloatTensor(test_acc_array).std())
        print('avg_acc: {}\tstd: {}'.format(np.mean(test_acc_array), std))
    np.save('/mnt/external_ssd/yanyajing2024/CADD_DCCNN_1/result/label_result/' + args.dataset + '_' + args.label_type + '_' + str(args.subjects) + '_' + args.data_split + '_pred.npy', pred_list)
    np.save('/mnt/external_ssd/yanyajing2024/CADD_DCCNN_1/result/label_result/' + args.dataset + '_' + args.label_type + '_' + str(args.subjects) + '_' + args.data_split + '_label.npy', label_list)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/label_result/' + args.dataset + args.label_type + str(args.subjects) + args.data_split + '_pred.npy', pred_list)
    # np.save('/home/bianning/Code/CADD_DCCNN_1/label_result/' + args.dataset + args.label_type + str(args.subjects) + args.data_split + '_label.npy', label_list)
    log_path = '/mnt/external_ssd/yanyajing2024/Code/CADD_DCCNN/log.csv'
    log(args, np.mean(train_loss_array), np.mean(train_acc_array), 
        np.mean(test_acc_array), np.mean(test_loss_array), std, log_path)

if __name__ == "__main__":
    T1 = time.time()
    main()
    T2 = time.time()
    get_time(T1, T2)