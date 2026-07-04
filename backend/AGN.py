import time
import logging
import numpy as np
import torch
import torch.nn.functional as F
from configparser import ConfigParser
from base import arg_parse, setup_seed, setup_device, setup_save_path, get_time
from base import DataSplit
from models.registry import build_model, MODEL_REGISTRY
from base import EarlyStopping, Accuracy, MeanLoss, AccStd, TSNE, Confusion, DataSaver



# 添加缺失的SEEDDataset类定义
class SEEDDataset:
    """模拟SEED数据集类"""

    def __init__(self, args):
        self.args = args
        # 这里添加实际的数据加载逻辑
        pass


class Trainer(object):
    def __init__(self, args):
        super(Trainer, self).__init__()
        self.args = args

        # 确保DataSplit可以访问SEEDDataset
        global SEEDDataset
        data_spliter = DataSplit(args)

        self.train_loader = data_spliter.train_loader
        self.test_loader = data_spliter.test_loader

        model_dict = MODEL_REGISTRY
        # 使用设备检测，而不是硬编码 cuda()
        self.device = torch.device(args.device if hasattr(args, 'device') else ('cuda' if torch.cuda.is_available() else 'cpu'))
        if self.device.type == 'cuda':
            torch.backends.cudnn.benchmark = True
        if args.model not in model_dict:
            raise ValueError(f"Unsupported model: {args.model}. Supported: {list(model_dict.keys())}")
        self.model = build_model(args.model, args).to(self.device)

        if args.model == 'EEGMatch':
            self.optimizer = torch.optim.AdamW(
                self.model.parameters(), lr=args.lr, weight_decay=1e-4,
            )
        else:
            self.optimizer = torch.optim.Adam(self.model.parameters(), lr=args.lr)
        self.lr_scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, patience=3 if args.model == 'ATGRNet' else 4)
        es_patience = 5 if args.model == 'ATGRNet' else 10
        self.early_stopping = EarlyStopping(patience=es_patience)
        self.mean_accuracy = Accuracy(args.nclass)
        self.mean_loss = MeanLoss(args.batch_size)
        self.acc_std = AccStd(args.batch_size)
        self.tsne_class = TSNE(args)
        self.tsne_domain = TSNE(args)
        self.confusion_matrix = Confusion(args)
        self.data_saver = DataSaver(args)

        print(args)
        logging.info(
            "===== 训练开始 | model=%s | feature=%s | split=%s | epochs=%s | device=%s | save_path=%s =====",
            args.model,
            args.feature_type,
            args.split_method,
            args.epochs,
            self.device,
            args.save_path,
        )
        logging.info("训练超参详情: %s", args)

    def run(self):
        self.acc_std.reset()
        self.confusion_matrix.reset()
        state_dict = None

        for epoch in range(self.args.epochs):
            self.train()
            acc, mloss = self.validation(epoch)
            self.acc_std.update(acc)

            is_best, is_terminate = self.early_stopping(acc)
            self.tsne_class.update_best(is_best)

            if self.args.have_domain:
                self.tsne_domain.update_best(is_best)

            self.confusion_matrix.update_best(is_best)

            if is_terminate:
                continue

            if is_best:
                state_dict = self.model.state_dict()

            self.lr_scheduler.step(mloss)

        max_acc, std = self.acc_std.compute()

        if self.args.save_model == 1:
            try:
                from metabci_integration.atgrnet_online import save_training_artifact

                checkpoint = state_dict if state_dict is not None else self.model.state_dict()
                artifact = save_training_artifact(checkpoint, self.args, max_acc)
                print(
                    "training artifact saved: "
                    f"model_path={artifact['model_path']} max_acc={max_acc:.4f}"
                )
                logging.info("training artifact saved: %s", artifact)
            except Exception as exc:
                logging.warning("模型保存失败（训练已完成）: %s", exc)
                print(f"warning: model save failed: {exc}")

        if self.args.save_tsne_cm == 1:
            try:
                if not self.args.have_domain:
                    self.data_saver.save_c(self.model, self.tsne_class.save())
                else:
                    self.data_saver.save_cd(
                        self.model,
                        self.tsne_class.save(),
                        self.tsne_domain.save(),
                    )
            except Exception as exc:
                logging.warning("t-SNE 结果保存失败（训练已完成）: %s", exc)
                print(f"warning: tsne save failed: {exc}")

        print(f'[{args.model}] max acc={max_acc} std={std}')
        logging.info('[%s] max acc=%s std=%s', args.model, max_acc, std)
        return max_acc, std

    def train(self):
        self.model.train()
        self.confusion_matrix.reset_train()

        for step, batch in enumerate(self.train_loader):
            if isinstance(batch[0], torch.Tensor):
                data, labels = batch[0].to(self.device), batch[1].to(self.device)
                logits = self.model(data)
                loss = self.model.loss(self.model, logits, labels)
                self.optimizer.zero_grad()
                loss.backward()
                if self.args.model == 'EEGMatch':
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()

                probs = F.softmax(logits[0], dim=-1).cpu().detach().numpy()
                self.tsne_class.update_train(logits[1], logits[2], labels.cpu().numpy())
                self.confusion_matrix.update_train(probs, labels.cpu().numpy())
            else:
                data = [i.to(self.device) for i in batch[0]]
                labels = [j.to(self.device) for j in batch[1]]
                logits = self.model(data)
                loss = self.model.loss(self.model, logits, labels)
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                probs = F.softmax(logits[0], dim=-1).cpu().detach().numpy()
                self.tsne_class.update_train(logits[2], logits[3], labels[0].cpu().numpy())
                self.tsne_domain.update_train(logits[2], logits[4], labels[1].cpu().numpy())
                self.confusion_matrix.update_train(probs, labels[0].cpu().numpy())

    def validation(self, epoch):
        self.model.eval()
        self.mean_loss.reset()
        self.mean_accuracy.reset()
        self.confusion_matrix.reset_test()

        with torch.no_grad():
            for step, batch in enumerate(self.test_loader):
                if isinstance(batch[0], torch.Tensor):
                    data, labels = batch[0].to(self.device), batch[1].to(self.device)
                    logits = self.model(data)
                    loss = self.model.loss(self.model, logits, labels)
                    probs = F.softmax(logits[0], dim=-1).cpu().detach().numpy()
                    self.mean_loss.update(loss.cpu().detach().numpy())
                    self.mean_accuracy.update(probs, labels.cpu().numpy())
                    self.tsne_class.update_test(logits[1], logits[2], labels.cpu().numpy())
                    self.confusion_matrix.update_test(probs, labels.cpu().numpy())
                else:
                    data = [i.to(self.device) for i in batch[0]]
                    labels = [j.to(self.device) for j in batch[1]]
                    logits = self.model(data)
                    loss = self.model.loss(self.model, logits, labels)
                    probs = F.softmax(logits[0], dim=-1).cpu().detach().numpy()
                    self.mean_loss.update(loss.cpu().detach().numpy())
                    self.mean_accuracy.update(probs, labels[0].cpu().numpy())
                    self.tsne_class.update_test(logits[2], logits[3], labels[0].cpu().numpy())
                    self.tsne_domain.update_test(logits[2], logits[4], labels[1].cpu().numpy())
                    self.confusion_matrix.update_test(probs, labels[0].cpu().numpy())

        acc = self.mean_accuracy.compute()
        mloss = self.mean_loss.compute()

        print(
            f"Validation Results [{self.args.model}] - Epoch: {epoch} acc: {acc:.4f} loss: {mloss:.4f}"
        )
        logging.info(
            "Validation Results [%s] - Epoch: %s acc: %.4f loss: %.4f",
            self.args.model,
            epoch,
            acc,
            mloss,
        )
        return acc, mloss



def debug(args):
    args.cur_sub_index = 0
    trainer = Trainer(args)
    max_acc, std = trainer.run()
    print(f'[{args.model}] debug is done, acc= {max_acc:.4f} std= {std:.4f}')
    logging.info('[%s] debug is done, acc= %.4f std= %.4f', args.model, max_acc, std)


def subject_independent(args):
    config = ConfigParser()
    config.read(args.config_path, encoding='UTF-8')
    acc_array = []
    sub_num = int(config[args.dataset]['sub_num'])

    if args.split_method == 'loso':
        for sub in range(sub_num):
            args.cur_sub_index = sub
            print(f'sub{sub} is start:')
            logging.info(f'sub{sub} is start:')

            trainer = Trainer(args)
            max_acc, std = trainer.run()

            print(f'sub{sub} is done, acc= {max_acc:.4f} std= {std:.4f}')
            logging.info(f'sub{sub} is done, acc= {max_acc:.4f} std= {std:.4f}')
            acc_array.append(max_acc)
            del trainer

        acc_array = np.array(acc_array)
        mean_acc = np.mean(acc_array)
        std_val = float(torch.FloatTensor(acc_array).std())

        print(f'LOSO mean acc = {mean_acc:.4f}, std = {std_val:.4f}')
        logging.info(f'LOSO mean acc = {mean_acc:.4f}, std = {std_val:.4f}')

    elif args.split_method == 'k_fold':
        one_fold_nums = int(sub_num / args.k_fold_nums)
        for fold in range(int(args.k_fold_nums)):
            args.cur_sub_index = fold * one_fold_nums
            print(f'fold{fold} is start:')
            logging.info(f'fold{fold} is start:')

            trainer = Trainer(args)
            max_acc, std = trainer.run()

            print(f'fold{fold} is done, acc= {max_acc:.4f} std= {std:.4f}')
            logging.info(f'fold{fold} is done, acc= {max_acc:.4f} std= {std:.4f}')
            acc_array.append(max_acc)
            del trainer

        acc_array = np.array(acc_array)
        mean_acc = np.mean(acc_array)
        std_val = float(torch.FloatTensor(acc_array).std())

        print(f'{args.k_fold_nums}_fold mean acc = {mean_acc:.4f}, std = {std_val:.4f}')
        logging.info(f'{args.k_fold_nums}_fold mean acc = {mean_acc:.4f}, std = {std_val:.4f}')


def subject_dependent(args):
    if args.split_method == 'by_sess':
        subject_dependent_sess(args)
    elif args.split_method == 'by_exp':
        subject_dependent_exp(args)


def subject_dependent_sess(args):
    config = ConfigParser()
    config.read(args.config_path, encoding='UTF-8')
    acc_array = []
    sub_num = int(config[args.dataset]['sub_num'])
    session_num = int(config[args.dataset]['session_num'])

    print(f"开始运行subject-dependent session模式：{sub_num}个被试者，{session_num}个session")
    logging.info(f"开始运行subject-dependent session模式：{sub_num}个被试者，{session_num}个session")

    for sub in range(sub_num):
        args.cur_sub_index = sub
        print(f'sub{sub} is start:')
        logging.info(f'sub{sub} is start:')

        for session in range(session_num):
            args.cur_session_index = session
            print(f'sub{sub} session{session} is start:')
            logging.info(f'sub{sub} session{session} is start:')

            try:
                trainer = Trainer(args)
                max_acc, std = trainer.run()

                print(f'sub{sub} session{session} is done, acc= {max_acc:.4f} std= {std:.4f}')
                logging.info(f'sub{sub} session{session} is done, acc= {max_acc:.4f} std= {std:.4f}')
                acc_array.append(max_acc)
                del trainer
            except Exception as e:
                print(f'sub{sub} session{session} 运行失败: {e}')
                logging.error(f'sub{sub} session{session} 运行失败: {e}')
                # 继续运行下一个session，而不是退出
                continue

    if len(acc_array) > 0:
        acc_array = np.array(acc_array)
        mean_acc = np.mean(acc_array)
        std_val = float(torch.FloatTensor(acc_array).std())

        print(f'SD by session mean acc = {mean_acc:.4f}, std = {std_val:.4f}')
        logging.info(f'SD by session mean acc = {mean_acc:.4f}, std = {std_val:.4f}')
    else:
        print("没有成功运行的session")
        logging.error("没有成功运行的session")


def subject_dependent_exp(args):
    config = ConfigParser()
    config.read(args.config_path, encoding='UTF-8')
    acc_array = []
    exp_num = int(config[args.dataset]['exp_num'])

    for exp in range(exp_num):
        args.cur_exp_index = exp
        print(f'exp{exp} is start:')
        logging.info(f'exp{exp} is start:')

        trainer = Trainer(args)
        max_acc, std = trainer.run()

        print(f'exp{exp} is done, acc= {max_acc:.4f} std= {std:.4f}')
        logging.info(f'exp{exp} is done, acc= {max_acc:.4f} std= {std:.4f}')
        acc_array.append(max_acc)
        del trainer

    acc_array = np.array(acc_array)
    mean_acc = np.mean(acc_array)
    std_val = float(torch.FloatTensor(acc_array).std())

    print(f'SD by exp mean acc = {mean_acc:.4f}, std = {std_val:.4f}')
    logging.info(f'SD by exp mean acc = {mean_acc:.4f}, std = {std_val:.4f}')


if __name__ == "__main__":
    T1 = time.time()
    args = arg_parse()
    setup_seed(args.seed)
    setup_device(args)
    setup_save_path(args)
    logging.info(
        "AGN 启动 | train_mode=%s | model=%s | feature=%s | save_path=%s",
        args.train_mode,
        args.model,
        args.feature_type,
        args.save_path,
    )

    train_mode = {
        'debug': debug,
        'si': subject_independent,
        'sd': subject_dependent
    }

    train = train_mode[args.train_mode]
    train(args)

    T2 = time.time()
    logging.info(get_time(T1, T2))