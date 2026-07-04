# MetaBCI 答辩用 curl 命令清单

> 后端默认地址：`http://localhost:5001`  
> 启动：`cd emo-system && python start.py`

---

## 1. 模块状态总览（必演示）

```bash
curl -s http://localhost:5001/api/metabci/status | python3 -m json.tool
```

关注字段：
- `modules.brainda` / `modules.brainstim` / `modules.brainflow`
- `brainda_strict.strict_function_count`（≥3 满分）
- `brainda_strict.meets_minimum_three`

---

## 2. brainda — 数据处理链路（3 个严格计分 API）

### 2.1 SEED 预处理

```bash
curl -s -X POST http://localhost:5001/api/metabci/brainda/seed-preprocess \
  -H "Content-Type: application/json" \
  -d '{"feature_type":"de_comp_4ch_1p5s","quick":true}' \
  | python3 -m json.tool
```

### 2.2 数据集加载（BaseDataset.get_data）

```bash
curl -s http://localhost:5001/api/metabci/brainda/seed-dataset \
  | python3 -m json.tool
```

### 2.3 LOSO 交叉验证划分（EnhancedLeaveOneGroupOut）

```bash
curl -s -X POST http://localhost:5001/api/metabci/brainda/loso \
  -H "Content-Type: application/json" \
  -d '{"held_out_subject":0}' \
  | python3 -m json.tool
```

### 2.4 Performance 分类评测

```bash
curl -s -X POST http://localhost:5001/api/metabci/brainda/evaluate \
  -H "Content-Type: application/json" \
  -d '{"held_out_subject":0}' \
  | python3 -m json.tool
```

### 2.5 DE 特征构建进度（可选）

```bash
curl -s http://localhost:5001/api/metabci/brainda/build-status | python3 -m json.tool
```

---

## 3. brainstim — 情绪实验范式

### 3.1 查询范式 4 步流程 + Marker 码

```bash
curl -s http://localhost:5001/api/metabci/brainstim/paradigm | python3 -m json.tool
```

关注字段：
- `steps[].marker_code` → 1/2/3/4
- `runtime.runtime_ready` → brainstim 是否可运行
- `strict_function_count` → 严格 API 计数

### 3.2 本地运行 brainstim GUI Demo

```bash
cd /home/lihanyue/home/workspace/emo-system/MetaBCI-master

# 无 GUI 探测（SSH/答辩前自检）
PYTHONPATH=. python demos/seed_emotion_brainstim_demo.py --dry-run

# 桌面环境运行范式窗口
PYTHONPATH=. python demos/seed_emotion_brainstim_demo.py --run --windowed --fast
```

---

## 4. brainflow — 在线情绪推理

### 4.1 设备源列表

```bash
curl -s http://localhost:5001/api/metabci/brainflow/device-sources | python3 -m json.tool
```

### 4.2 启动在线推理流

```bash
curl -s -X POST http://localhost:5001/api/metabci/brainflow/start \
  -H "Content-Type: application/json" \
  -d '{"model_name":"DGConformer","device_source":"seed_replay"}' \
  | python3 -m json.tool
```

### 4.3 查询流状态

```bash
curl -s http://localhost:5001/api/metabci/brainflow/status | python3 -m json.tool
```

### 4.4 停止在线流

```bash
curl -s -X POST http://localhost:5001/api/metabci/brainflow/stop | python3 -m json.tool
```

---

## 5. 业务 API（前端对应操作）

### 5.1 数据处理（Step1 按钮）

```bash
curl -s -X POST http://localhost:5001/api/data-preprocessing \
  -H "Content-Type: application/json" \
  -d '{"filename":"seed_demo","feature_type":"de_comp_4ch_1p5s"}' \
  | python3 -m json.tool
```

### 5.2 特征学习训练

```bash
curl -s -X POST http://localhost:5001/api/feature-learning \
  -H "Content-Type: application/json" \
  -d '{"model_name":"DGConformer","epochs":5}' \
  | python3 -m json.tool
```

### 5.3 情绪识别

```bash
curl -s -X POST http://localhost:5001/api/emotion-recognition \
  -H "Content-Type: application/json" \
  -d '{"model_name":"DGConformer"}' \
  | python3 -m json.tool
```

### 5.4 生成脑地形图

```bash
curl -s -X POST http://localhost:5001/api/generate-topomaps | python3 -m json.tool
```

### 5.5 健康检查

```bash
curl -s http://localhost:5001/api/health | python3 -m json.tool
```

---

## 6. 推荐答辩演示顺序

| 顺序 | 操作 | 说明 |
|------|------|------|
| 1 | `curl .../metabci/status` | 展示三模块可用 + brainda ≥3 |
| 2 | 前端 Step1「启动数据流水线」 | brainda 预处理 + brainstim 范式面板 |
| 3 | `curl .../brainstim/paradigm` | 展示 4 步 marker |
| 4 | `python demos/seed_emotion_brainstim_demo.py --dry-run` | brainstim 严格 API 探测 |
| 5 | 前端 Step2 特征学习 → Step3 情绪识别 | brainflow 在线推理 |
| 6 | `curl .../brainflow/status` | 展示实时推理状态 |
| 7 | 前端 Step4 可视化展示 | t-SNE + 训练曲线 |

---

## 7. 环境准备（答辩前一次性）

```bash
cd /home/lihanyue/home/workspace/emo-system/MetaBCI-master
pip install -e .[brainda,brainflow,brainstim]

export PYTHONPATH=/home/lihanyue/home/workspace/emo-system/MetaBCI-master:$PYTHONPATH

# 验证
python -c "import metabci.brainda; import metabci.brainstim; import metabci.brainflow; print('OK')"
```

---

## 8. Marker 码速查表

| Step | 名称 | Marker 名 | 码值 | 时长 |
|------|------|-----------|------|------|
| 1 | 基线采集 | baseline | **1** | 30s |
| 2 | 情绪刺激 | emotion_stimulus | **2** | 90s |
| 3 | EEG 同步 | eeg_marker | **3** | 事件 |
| 4 | 在线反馈 | online_feedback | **4** | 事件 |

情绪块附加 marker（Demo 脚本内）：
- 积极 → **21**
- 中性 → **22**
- 消极 → **23**
