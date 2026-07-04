#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import torch
import numpy as np
import matplotlib.pyplot as plt
import mne
from mne.viz import plot_topomap
from scipy.signal import welch
from scipy.stats import zscore
import os
import sys
from pathlib import Path

def load_eeg_data(data_path):
    """加载EEG数据"""
    try:
        data = torch.load(data_path)
        print(f"数据形状: {data.shape}")
        return data
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def extract_frequency_bands(eeg_data, sfreq=1000):
    """提取五个频率段的EEG数据"""
    # 定义频率段
    frequency_bands = {
        'delta': (1, 4),       # 1-4 Hz
        'theta': (4, 8),       # 4-8 Hz
        'alpha': (8, 14),      # 8-14 Hz
        'beta': (14, 31),      # 14-31 Hz
        'gamma': (31, 50)      # 31-50 Hz
    }
    
    # 处理不同维度的数据
    if len(eeg_data.shape) == 6:
        # (subjects, sessions, trials, channels, time, frequency_bands)
        print(f"原始数据形状: {eeg_data.shape}")
        
        # 取第一个被试者的第一个session的第一个trial的数据
        # 数据形状: (15, 3, 15, 62, 265, 5) -> 取 (0, 0, 0, :, :, :) -> (62, 265, 5)
        data = eeg_data[0, 0, 0, :, :, :].numpy()  # (channels, time, frequency_bands)
        print(f"处理后的数据形状: {data.shape}")
        
        # 对时间维度求平均，得到每个通道在每个频率段的平均功率
        # (62, 265, 5) -> (62, 5)
        data_mean = np.mean(data, axis=1)  # 对时间维度求平均
        print(f"时间平均后的数据形状: {data_mean.shape}")
        
        # 直接使用频率段数据
        frequency_data = {}
        band_names = ['delta', 'theta', 'alpha', 'beta', 'gamma']
        for i, band_name in enumerate(band_names):
            if i < data_mean.shape[1]:
                frequency_data[band_name] = data_mean[:, i]
                print(f"{band_name}频段数据形状: {frequency_data[band_name].shape}")
            else:
                # 如果频率段数量不匹配，使用方差作为替代
                frequency_data[band_name] = np.var(data_mean, axis=1)
        
        return frequency_data
        
    elif len(eeg_data.shape) == 5:
        # (subjects, sessions, channels, time, features)
        data = eeg_data[0, 0, :, :, :].mean(dim=(1, 2)).numpy()  # 取第一个被试者的第一个session
    elif len(eeg_data.shape) == 4:
        # (subjects, sessions, channels, time)
        data = eeg_data[0, 0, :, :].numpy()  # 取第一个被试者的第一个session
    elif len(eeg_data.shape) == 3:
        # (subjects, channels, time)
        data = eeg_data[0, :, :].numpy()  # 取第一个被试者
    elif len(eeg_data.shape) == 2:
        # (channels, time)
        data = eeg_data.numpy()
    else:
        raise ValueError(f"不支持的数据形状: {eeg_data.shape}")
    
    print(f"处理的数据形状: {data.shape}")
    
    # 如果数据时间太短，我们需要扩展数据
    if data.shape[1] < 1000:
        # 重复数据以增加时间长度
        repeat_times = max(1, 1000 // data.shape[1])
        data = np.tile(data, (1, repeat_times))
        print(f"数据已扩展到: {data.shape}")
    
    # 使用Welch方法计算功率谱密度
    frequency_data = {}
    for band_name, (low_freq, high_freq) in frequency_bands.items():
        print(f"提取{band_name}频段 ({low_freq}-{high_freq} Hz)...")
        
        try:
            # 计算每个通道的功率谱密度
            powers = []
            for ch_data in data:
                f, Pxx = welch(ch_data, fs=sfreq, nperseg=min(256, len(ch_data)//4))
                # 找到频段内的功率
                mask = (f >= low_freq) & (f <= high_freq)
                if np.any(mask):
                    power = np.trapz(Pxx[mask], f[mask])
                else:
                    power = np.var(ch_data)  # 如果没有找到频段，使用方差
                powers.append(np.log(power + 1e-8))  # 使用log能量
            
            frequency_data[band_name] = np.array(powers)
        except Exception as e:
            print(f"处理{band_name}频段失败: {e}")
            # 使用原始数据的方差作为替代
            frequency_data[band_name] = np.var(data, axis=1)
    
    return frequency_data

def create_topomap(data, title, save_path):
    """创建拓扑图并保存"""
    try:
        # 创建图形
        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 使用标准的62通道电极位置
        channels = [
            'Fp1','AF3','F7','F3','FC1','FC5','T7','C3','CP1','CP5',
            'P7','P3','PO3','O1','Oz','Pz','Fp2','AF4','Fz','F4',
            'F8','FC2','FC6','Cz','C4','T8','CP2','CP6','P4','P8',
            'PO4','O2','F5','F1','FT9','FT7','FC3','C5','C1','TP7',
            'CP3','P5','P1','PO7','POz','PO8','P2','P6','TP8','C2',
            'C6','FC4','FT8','F6','F2','AF7','AFz','AF8','Fpz','CPz',
            'PO9','PO10'
        ]
        
        # 确保数据长度与通道数量匹配
        if len(data) != len(channels):
            print(f"数据长度({len(data)})与通道数量({len(channels)})不匹配，使用前{len(channels)}个数据点")
            data = data[:len(channels)]
        
        # 创建info对象
        info = mne.create_info(channels[:len(data)], 1000, 'eeg')
        
        # 设置标准电极位置
        try:
            # 尝试使用标准1020电极位置
            montage = mne.channels.make_standard_montage("standard_1020")
            info.set_montage(montage)
        except Exception as e:
            print(f"设置标准电极位置失败: {e}")
            # 使用自定义位置
            try:
                # 尝试使用biosemi62电极位置
                montage = mne.channels.make_standard_montage("biosemi62")
                info.set_montage(montage)
            except Exception as e2:
                print(f"设置biosemi62电极位置失败: {e2}")
                # 使用简化的圆形排列
                pos = []
                radius = 0.4
                for i in range(len(data)):
                    angle = 2 * np.pi * i / len(data)
                    x = radius * np.cos(angle)
                    y = radius * np.sin(angle)
                    pos.append([x, y, 0])
                
                ch_pos = dict(zip(channels[:len(data)], pos))
                info.set_montage(mne.channels.make_dig_montage(
                    ch_pos=ch_pos,
                    coord_frame='head'
                ))
        
        # 标准化数据
        data_zscore = zscore(data)
        
        # 创建拓扑图
        try:
            im, _ = mne.viz.plot_topomap(
                data_zscore, info, axes=ax, show=False,
                cmap='RdBu_r', contours=0,
                sensors=True, outlines='head'
            )
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.colorbar(im, ax=ax, shrink=0.8)
        except Exception as e:
            print(f"标准拓扑图方法失败: {e}")
            # 使用备用方法
            try:
                plot_topomap(data_zscore, info, axes=ax, show=False,
                           sensors=True, contours=6, outlines='head')
                ax.set_title(title, fontsize=14, fontweight='bold')
            except Exception as e2:
                print(f"备用拓扑图方法也失败: {e2}")
                # 使用最简单的散点图方法
                ax.scatter(range(len(data)), data_zscore, c=data_zscore, 
                          cmap='RdBu_r', s=100, edgecolors='black')
                ax.set_title(title, fontsize=14, fontweight='bold')
                ax.set_xlabel('Channel Index')
                ax.set_ylabel('Z-score')
        
        # 保存图片
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"拓扑图已保存到: {save_path}")
        return True
    except Exception as e:
        print(f"创建拓扑图失败: {e}")
        return False

def generate_topomaps(data_path, output_dir):
    """生成五个频率段的拓扑图"""
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    print("加载EEG数据...")
    eeg_data = load_eeg_data(data_path)
    if eeg_data is None:
        return False
    
    # 提取频率段数据
    print("提取频率段数据...")
    frequency_data = extract_frequency_bands(eeg_data)
    
    # 生成拓扑图
    frequency_bands = {
        'delta': 'Delta (1-4 Hz)',
        'theta': 'Theta (4-8 Hz)',
        'alpha': 'Alpha (8-14 Hz)',
        'beta': 'Beta (14-31 Hz)',
        'gamma': 'Gamma (31-50 Hz)'
    }
    
    success_count = 0
    for band_name, band_title in frequency_bands.items():
        print(f"生成{band_name}频段拓扑图...")
        
        save_path = output_path / f"{band_name}_topomap.png"
        if create_topomap(frequency_data[band_name], band_title, save_path):
            success_count += 1
    
    print(f"成功生成 {success_count}/5 个拓扑图")
    return success_count == 5

def main():
    """主函数"""
    # 数据路径 - 使用相对路径
    data_path = "seed/de/data.pt"
    
    # 输出目录 - 使用绝对路径
    output_dir = r"C:\Users\62566\Desktop\科研\MetaBCI\emo-system - 副本\emo-system\src\assets\module1"
    
    print("开始生成EEG拓扑图...")
    print(f"数据路径: {data_path}")
    print(f"输出目录: {output_dir}")
    
    # 检查数据文件是否存在
    if not os.path.exists(data_path):
        print(f"数据文件不存在: {data_path}")
        # 尝试使用绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, "seed", "de", "data.pt")
        if not os.path.exists(data_path):
            print(f"数据文件不存在: {data_path}")
            return False
        else:
            print(f"找到数据文件: {data_path}")
    
    # 生成拓扑图
    success = generate_topomaps(data_path, output_dir)
    
    if success:
        print("所有拓扑图生成完成！")
    else:
        print("拓扑图生成失败！")
    
    return success

if __name__ == "__main__":
    main()
