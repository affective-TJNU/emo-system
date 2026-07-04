# 初赛完整演示视频录制指南（无电极帽）

本指南适用于 **不连接 Neuroscan 电极帽**，但需展示完整 MetaBCI 功能链路的初赛录屏。

## 可以录什么

| 模块 | 无电极帽能否演示 | 说明 |
|------|------------------|------|
| brainstim 图片刺激 | ✅ | PsychoPy `ImageStim` 真实弹窗呈现 |
| LSL Marker | ✅ | `LsLPort.setData` 发送 #1~#4, #21~#23 |
| brainda 数据处理 | ✅ | SEED 数据集回放 |
| brainflow 在线推理 | ✅ | `neuroscan_sim` 模拟 40 导 → AF3/AF4/F3/F4 |
| Neuroscan 40 导接入 | ✅（预留） | 界面展示 `neuroscan_lsl`，说明待接硬件 |

---

## 一、启动环境（本地桌面，需有图形界面）

```bash
# 终端 1 — 后端
cd ~/home/workspace/emo-system/backend
conda activate gkan
python run.py

# 终端 2 — 前端
cd ~/home/workspace/emo-system
npm run dev

# 若刺激图片不存在，先生成（只需一次）
conda activate gkan
python scripts/generate_emotion_stimuli.py
```

浏览器打开：`http://localhost:5173/home`

---

## 二、PsychoPy 真实图片刺激（层 1，brainstim 计分用）

```bash
# 终端 3 — 必须在本地桌面终端（有 DISPLAY）
cd ~/home/workspace/emo-system/MetaBCI-master
conda activate gkan
export DISPLAY=:0
PYTHONPATH=. python demos/seed_emotion_brainstim_demo.py --run --windowed --fast
```

操作：
1. 弹出 brainstim 启动屏 → 按 **Enter** 运行 `SEEDPassiveEmotion`
2. 依次看到：**注视十字** → **积极/中性/消极图片** → marker 同步 → 反馈提示
3. **Esc** 可随时中断

录屏建议：**Web 大屏 + PsychoPy 窗口并排**，体现 brainstim 框架真实刺激。

---

## 三、Web 大屏演示顺序（约 3~5 分钟）

### 1. 数据处理（Step 0）
- 展示 **Neuroscan 40 导设备接入（预留）** 条
- 展示 **情绪图片刺激预览** 缩略图（接口已就绪）
- 点击 **「验证 brainstim API」** → 显示 **严格 API 3/3**
- 点击 **「模拟范式运行」** → 同步展示：
  - 基线十字
  - 三类情绪图片
  - LSL Marker 事件流

### 2. 数据处理流水线
- 点击开始处理 → brainda 预处理进度

### 3. 特征学习 / 模型选择
- 按正常流程点几步（可加速）

### 4. 情绪识别（brainflow 在线）
- 启动在线推理（`device_source: neuroscan_sim`）
- 展示三分类概率实时更新

### 5. 终端自检（可选同框）
```bash
python scripts/preliminary_metabci_verify.py
```

---

## 四、答辩/字幕可强调的一句话

> 「当前无电极帽，EEG 由 Neuroscan 40 导模拟源与 SEED 回放驱动；情绪诱发由 MetaBCI brainstim 的 PsychoPy ImageStim 呈现，marker 经 LsLPort 与 brainflow 对齐；`neuroscan_lsl` 接口已预留，接入真实 LSL 流即可切换。」

---

## 五、常见问题

**Q: SSH 远程能跑 PsychoPy 吗？**  
A: 录视频不行，需本地桌面 `export DISPLAY=:0`。Web 演示可在远程完成。

**Q: 严格 API 只有 2/3？**  
A: `Experiment.register_paradigm` 需要 DISPLAY。在本地桌面点「验证 brainstim API」即可 3/3。

**Q: 图片能换成 SEED 原视频截帧吗？**  
A: 可以。替换 `MetaBCI-master/stimuli/seed_emotion/{positive,neutral,negative}/` 下 PNG 即可，无需改代码。
