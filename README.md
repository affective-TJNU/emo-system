# emo-system

基于 [MetaBCI](https://github.com/TBC-TJU/MetaBCI) 的脑电情绪识别与在线反馈系统（MetaBCI 创新应用开发赛项）。

## 仓库来源

| 项目 | 地址 |
|------|------|
| 本队开源仓库 | https://github.com/affective-TJNU/emo-system |
| Fork 自 MetaBCI 官方 | https://github.com/TBC-TJU/MetaBCI |

## 项目概述

依托 MetaBCI 三子平台（brainstim / brainflow / brainda），构建「数据采集与预处理 → 特征学习 → 在线情绪推理 → 可视化分析」四步闭环 Web 系统，支持 SEED 公开数据集与 Neuroscan 自采双模式。

## 快速启动

```bash
# 1. 安装 MetaBCI（在 MetaBCI-master 目录）
cd MetaBCI-master && pip install -e ".[brainda,brainflow,brainstim]"
# 2.将seed原始数据processed EEG文件放至emo-system/backend/seed路径下
# 3. 回到项目根目录一键启动（后端 5001 + 前端 5173）
cd .. && python start.py
```
详细环境配置、数据准备与功能验证见 [`docs/项目测试说明文档.md`](docs/项目测试说明文档.md)。

## 主要目录

| 目录 | 说明 |
|------|------|
| `MetaBCI-master/` | Fork 后的 MetaBCI 平台（含 SEED 数据集、Demo 扩展） |
| `backend/` | Flask 后端、模型训练与 MetaBCI 集成层 |
| `src/` | Vue 前端 |
| `docs/` | 项目测试说明、答辩 curl 清单、录屏指南 |
| `scripts/` | MetaBCI 三模块自检脚本 |

## 测试与 Demo

| 用途 | 路径 |
|------|------|
| MetaBCI 三模块 API 自检 | `scripts/preliminary_metabci_verify.py` |
| brainstim 情绪范式 Demo | `MetaBCI-master/demos/seed_emotion_brainstim_demo.py` |
| brainda 数据集 Demo | `MetaBCI-master/demos/seed_emotion_demo.py` |
| API 测试命令清单 | `docs/METABCI_DEFENSE_CURL.md` |

## 许可证

MetaBCI 本体遵循 MIT 许可证，见 [`MetaBCI-master/LICENSE`](MetaBCI-master/LICENSE)。
