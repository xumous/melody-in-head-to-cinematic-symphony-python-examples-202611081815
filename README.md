# 脑海中的旋律 → 好莱坞史诗交响（4 分钟）

**语言**：[中文](README.md) · [English](README_EN.md) · [日本語](README_JA.md) · [Français](README_FR.md)

把一个"脑海里挥之不去的简谱旋律"做成 4 分钟、可上流媒体的电影史诗配乐：纯 Python 渲染，采样用 Sonatina Symphonic
Orchestra（SSO）+ `pysfizz`，混音/母带全部用 NumPy + SciPy 手写 DSP 完成，不使用任何 DAW。

最终成品：**240.00 s / −15.35 LUFS / −1.02 dBTP / LRA 15.0 LU**，8 段结构、6 条分轨、格式 1 MIDI。

---

## 1. 成品在哪

| 文件                                 | 说明                                                                                           |
|------------------------------------|----------------------------------------------------------------------------------------------|
| `epic_final.flac`                  | 最终母带（无损，24-bit 源转码）                                                                          |
| `epic_final.mp3`                   | 最终母带（流媒体分发版）                                                                                 |
| `epic_final.mid`                   | 格式 1 / 6 轨 / 480 TPQ，ch0 主旋律铜管、ch1 低音铜管、ch2 打击乐、ch3 弦乐、ch4 合唱                                |
| `premaster.flac` / `premaster.mp3` | 母带前版本（未限幅、未对齐响度）                                                                             |
| `spectrogram_final.png`            | 频谱图 + 平均频谱（验收用）                                                                              |
| `loudness_report.txt`              | 自动生成的渲染报告（响度、峰值、频段、段落 RMS、分轨、验收结论）                                                           |
| `stems/*.flac` / `stems/*.mp3`     | 6 条分轨：`melody_lead` / `brass` / `low_brass_bass` / `strings` / `percussion` / `choir_hybrid` |
| `probe.flac` / `probe.mp3`         | 音源可用性试听：铜管大三和弦 + 定音鼓 + 大鼓/小军鼓 + 弦乐 tremolo + 合唱                                              |

`renders（就是喇叭从弱到强）/` 目录里保存着 v1–v5 每一版的完整产物（含 `epic_final.wav`、`premaster.wav`
、分轨、频谱图、报告），可以直接对比"喇叭从弱到强"的进化过程；其中 `v2（最好听）` 是主观听感最好的一版，`v5` 是客观指标与力度阶梯都达标的交付版。

---

## 2. 快速开始

### 2.1 环境依赖

```
Python 3.14（实测）
numpy  scipy  soundfile  matplotlib  pyloudnorm  requests  pysfizz==0.1.3
ffmpeg（仅交叉验证与格式转码用，非必需）
```

`pysfizz` 是 sfizz 采样引擎的 Python 绑定，负责按 MIDI 事件离屏渲染 SFZ 音色；没有它 `epic_engine.py`
会降级为 `Synth = None`（此时只能跑 `tools_selftest.py` 的桩采样器链路）。

### 2.2 采样库

- 采样库本体已随仓库放在 `soundfonts/Sonatina Symphonic Orchestra/`（641 个文件，约 283 MB，是整包 1.39 GB 的**按需子集**）。
- **关键坑**：`pysfizz` 只能打开纯 ASCII 路径。项目目录含中文时会抛
  `No mapping for the Unicode character exists in the target multi-byte code page`。
  解决办法是建一个 ASCII junction 指向采样库：

  ```powershell
  cmd /c mklink /J D:\_sso "D:\MasterXu2026091\melody-in-head-to-cinematic-symphony-python-examples-202611081815\soundfonts\Sonatina Symphonic Orchestra"
  ```

  `epic_engine.SSO_ROOT` 会优先使用 `D:/_sso`，不存在时才回落到项目内路径。

### 2.3 渲染与归档

```powershell
# 1) 全链路自检（不需要采样，桩采样器，约 1 分钟）
python tools_selftest.py

# 2) 音源最小验证（生成 probe.wav，检查是不是"真铜管"）
python probe_sso.py
python tools_check_probe.py

# 3) 跑最终版本（v5，写入 renders/v5）
python v5_epic_orchestrator.py

# 4) 把 v5 产物拷到仓库根目录并做最终检查
python tools_package.py v5

# 5) ffmpeg 交叉验证响度（结果追加到 loudness_report.txt）
python tools_ffmpeg_verify.py
```

> 注意：`v1..v5` 和 `tools_package.py` 里硬编码了输出目录 `renders/vN`
> ，而当前归档目录被改名成了 `renders（就是喇叭从弱到强）`。重新渲染会在根目录**新建**一个 `renders/`
> 文件夹，不会覆盖旧归档；需要覆盖归档时请自行先改路径。

---

## 3. 目录结构

```
melody-in-head-to-cinematic-symphony-python-examples-202611081815/
├── epic_engine.py                  # ★ 核心库：采样器 + 编曲器 + 混音 + DSP + 母带 + MIDI + 报告
├── v1_epic_orchestrator.py         # v1：四幕骨架（PROFILE 基线）
├── v2_epic_orchestrator.py         # v2：频谱与平衡（继承 v1 PROFILE）
├── v3_epic_orchestrator.py         # v3：亮度与织体（继承 v2）
├── v4_epic_orchestrator.py         # v4：动态落差与母带（继承 v3）
├── v5_epic_orchestrator.py         # v5：最终交付（继承 v4）★ 推荐入口
├── original_script.py              # 原 4 分钟交响版脚本的字节级只读副本（44.1 kHz 合成器版）
├── RESEARCH_NOTES.md               # 30 条"为什么史诗"的可执行规则 + 混音参数 + 实测约束
│
├── first/                          # 项目起点：三份单文件脚本及其产物
│   ├── 我脑海里的一段旋律_python_20261107_65b3ca.py/.exe        # 钢琴单旋律 + WAV/MIDI
│   ├── 我脑海里的一段旋律扩展4分钟_python_20261108_050346.py/.exe  # 4 分钟钢琴版（弱起处理）
│   ├── 我脑海里的一段旋律扩展4分钟最初交响版_python_20261108_f84da8.py/.exe # 最初交响版（= original_script.py）
│   └── piano.flac/.mid/.mp3  piano_4min.*  piano_epic_4min.*    # 上面脚本的渲染产物
│
├── soundfonts/Sonatina Symphonic Orchestra/   # SSO v4.0 按需子集（Brass/Strings/Woodwinds/Percussion/Chorus + Samples*）
├── logs/                           # 下载与自检日志
│   ├── download.log / download.err         # 整包 zip 方案（BadZipFile，已放弃）
│   ├── fetch.log / fetch_samples.log       # SFZ 与采样抓取过程（含失败重试记录）
│   ├── sample_list.json                    # 最终要下载的 702 条采样清单（按优先级排序）
│   └── selftest.log                        # 桩采样器自检输出（47 s 跑完）
│
├── renders（就是喇叭从弱到强）/    # 每版完整产物归档
│   ├── selftest/                   # 桩采样器自检产物
│   ├── v1/ v2（最好听）/ v3/ v4/ v5/   # 每版：epic_final.* / premaster.* / stems/ / 频谱图 / 报告
│
├── stems/                          # 最终 6 条分轨（flac + mp3）
├── __pycache__/                    # Python 字节码缓存
└── README*.md                      # 本说明（中/英/日/法）
```

### 3.1 工具脚本（`tools_*.py`，全部是独立可执行的诊断/搬运小工具）

| 脚本                       | 作用                                                                                                                                 |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| `tools_download_sso.py`  | 整包下载方案：gh-proxy 镜像 + Range 断点续传 + zip 校验。实测在 348 MB 处停滞，最终未采用，仅留作备选                                                                |
| `tools_probe_mirrors.py` | 并发测速 6 个 GitHub 加速镜像（ghfast / gh-proxy / moeyy / gitmirror / kgithub / ghproxy.net），输出 kB/s                                        |
| `tools_fetch_subset.py`  | 按白名单抓 SFZ 文本 → 递归解析 `#include` → 收集 `sample=` 路径 → 16 并发下载采样；目录结构与仓库保持一致，sfizz 才能按相对路径找到文件                                         |
| `tools_fetch_samples.py` | **最终可用方案**：导入 `epic_engine.INST` 只下载真正用到的音色采样；多 jsDelivr CDN 轮换 + `requests` Session 复用 + Range 续传 + 三级优先级（打击乐→铜管→弦乐→木管→合唱）+ 3 轮补漏 |
| `tools_move_samples.py`  | 修复采样被误放进各乐器子目录的问题（SSO 的 `sample=../Samples/...` 是相对主 SFZ 目录解析的）                                                                    |
| `tools_status.py`        | 逐个加载 `epic_engine.INST` 里的 SFZ，打印是否成功与可演奏音域（确认子集够用）                                                                                |
| `probe_sso.py`           | 最小可听验证：C 大三和弦（小号/圆号/长号/大号）+ 定音鼓 + 大鼓/小军鼓 + 弦乐 tremolo + 合唱 → `probe.wav`                                                           |
| `tools_check_probe.py`   | 分析 `probe.wav` 各段 RMS、峰值与频谱质心，证明"是采样不是正弦"                                                                                          |
| `tools_selftest.py`      | 桩采样器（噪声代替 SSO）跑完整链路：编排→分轨→DSP→母带→MIDI→报告，47 s 内验证代码路径与内存                                                                           |
| `tools_diagnose.py`      | 分轨峰值/RMS、8 段 RMS 曲线、整曲频段分布                                                                                                         |
| `tools_bands.py`         | 分轨 + 成品各频段能量占比（用于定位"高频丢失"）                                                                                                         |
| `tools_check_midi.py`    | 解析 MIDI 头、轨数、TPQ、每通道 note-on 数量、末事件 tick 与时长                                                                                       |
| `tools_ffmpeg_verify.py` | 用 `ffmpeg loudnorm` 交叉验证 LUFS / True Peak / LRA，并追加写入 `loudness_report.txt`                                                        |
| `tools_sample_bands.py`  | 直接分析 SSO 原始采样文件频谱（判断"是库偏暗还是渲染链偏暗"，路径写死 `D:/_sso`）                                                                                  |
| `tools_hf_test.py`       | 逐环节对比频谱：原始采样 / HP+EQ / 压缩 / 母带链，用于定位高频损失发生在哪一步                                                                                     |
| `tools_package.py`       | 把指定版本（默认 v5）的成品、报告、频谱图、分轨拷到仓库根目录并做最终检查                                                                                             |

---

## 4. 音乐设计（写进代码的硬规则）

### 4.1 结构：8 段 × 30 s（96 拍 @ 192 BPM）

| # | 段落     | 时长        | 配器与功能                                                                   |
|---|--------|-----------|-------------------------------------------------------------------------|
| 0 | Intro  | 0:00–0:30 | 弦乐 tremolo + 大提琴低音长音 + sub bass + 心跳大鼓 + 远处定音鼓 + 竖琴 + 长笛主题预告 + 滚奏 riser |
| 1 | A1     | 0:30–1:00 | **圆号独奏主旋律**（第一次陈述）+ 弦乐温暖层 + 低音铜管长音 + 定音鼓心跳 + 弱小军鼓                       |
| 2 | B      | 1:00–1:30 | **长笛主旋律**（双簧管弱叠）+ 铜管退为和声长音，全曲唯一的"呼吸段"                                   |
| 3 | A2     | 1:30–2:00 | **小号接过主旋律** + 圆号助奏/对位 + 低音铜管八分音符固定音型 + 小军鼓加密                            |
| 4 | C1     | 2:00–2:30 | **小号组齐奏** + 弦乐 ostinato + tremolo + 全打击乐；第 20 小节起转 **D♭（那不勒斯 ♭II）**     |
| 5 | C2     | 2:30–3:00 | **全铜管八度齐奏 + 合唱 + 木管高八度 + 电子 kick**；三连音固定音型；尾部 V→Cm 终止                   |
| 6 | Outro1 | 3:00–3:30 | 圆号回到主旋律（退潮），织体逐层撤走，铜管和声收拢                                               |
| 7 | Outro2 | 3:30–4:00 | 独奏小提琴/长笛回响，V（G）两段渐强 → **C 大三和弦（Picardy third）终止一击** + 3.5 s 自然衰减        |

同一主旋律 4 次陈述、力度与铜管编组逐级加码：圆号 → 小号 → 铜管齐奏 → 全铜管 + 合唱。

### 4.2 旋律与和声

- 旋律用简谱记号存表：`PICKUP`（2 拍弱起）+ `MAIN`（77
  拍主体），记号规则见 `first/我脑海里的一段旋律_python_20261107_65b3ca.py` 头部注释（`-` 延长拍、`【】` 时值减半、`{}`
  连奏、`————>` 渐弱收尾）。
- 主调 C 和声小调，核心进行 `Cm – A♭ – Fm – G`（每 2 小节一换，12 组循环）；C1 尾部插入 `D♭`、Outro2 结尾 `G → C`。
- 主旋律音区设计为铜管最辉煌的位置（小号 F4–C5 一线），因此"同一旋律换编组"就能自然变"大"。

---

## 5. 引擎架构

```
SSO 采样（pysfizz / SFZ）
        │  Sampler.note(inst, pitch, vel, on_dur, tail)  → 带磁盘缓存的单音渲染
        ▼
Orchestrator（8 个 sec_* 方法）──► Mixer（6 条 bus + 2 路混响 send + kick 侧链键）
        │                          MIDI 事件同步记录
        ▼
process_buses（分轨 DSP）──► mix_down（叠加 + 混响 wet 曲线）──► premaster.wav
        │
        ▼
master_chain：① 20 Hz HP ② 2–4 kHz 轻收 ③ 6 kHz shelf ④ 胶水压缩 GR≤3
              ⑤ tanh 饱和 THD 1–2% ⑥ 响度对齐 + True Peak 限幅迭代 ⑦ 3.5 s 淡出
        │
        ▼
epic_final.wav + epic_final.mid + spectrogram_final.png + loudness_report.txt
```

- **所有音乐参数都在 `PROFILE` 字典里**：乐器选择、力度、织体、打击乐密度、bus 电平、混响、母带目标。v1–v5 脚本只改 `PROFILE`
  ，不改引擎。
- **6 条 bus**：`lead`（主旋律铜管/长笛/小提琴）、`brass`（铜管和声）、`low`（低音铜管 + sub +
  低音弦乐）、`strings`、`perc`、`choir`。
- **hybrid 层**：`synth_harp` / `synth_bass_inst` / `synth_choir` / `synth_bass_drum`
  是原脚本遗留的合成器音色，叠在采样层上补"电子 kick 与合唱厚度"。
- **采样缓存**：`Sampler` 以 `inst|pitch|vel|on_dur|tail` 为键缓存到 `cache/*.npz`，重复音色不重复渲染。

### 5.1 分轨处理（实测调好的数值）

| Bus              | 处理                                                                                                                                                |
|------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| `brass` / `lead` | HP 80 Hz（18 dB/oct）→ 200–400 Hz −1.5 dB（去盒音）→ 2–5 kHz +2.5 dB（presence）→ 5 kHz shelf +3.5 dB（air）→ 可选谐波激励器 → 2:1 / 30 ms / 250 ms 胶水压缩（GR 1–2 dB） |
| `low`            | **不 HP**，保住 40–100 Hz → kick 侧链 ducking（−18 dB / 3:1 / 5 ms / 120 ms，深度 5–6.5 dB）→ 2:1 压缩                                                         |
| `strings`        | HP 80 Hz → 150–350 Hz −2 dB → 4 kHz shelf +1.5 dB → 激励器（比铜管低 4 dB）→ 1.5:1 压缩                                                                      |
| `perc`           | 300–500 Hz 动态衰减 −2 dB（避让铜管中低）→ HP 28 Hz → 3–6 kHz +2 dB                                                                                           |
| `choir`          | HP 60 Hz → 300–600 Hz −1.5 dB → 4 kHz shelf +1 dB                                                                                                 |
| `reverb`         | 铜管/弦乐/合唱长 IR（2.8–3.3 s），打击乐短 IR（1.2–1.6 s）；C2 wet 比 A1 **低约 25–28%**（爆发段要"干"，保住冲击力）                                                               |

### 5.2 母带链

20 Hz 高通（24 dB/oct）→ 2–4 kHz −0.8 dB → 6 kHz shelf +1.5 dB → 胶水压缩 1.8:1 / 35 ms / 250 ms / GR ≤ 3 dB → `tanh`
轻饱和（THD 1–2%）→ 响度对齐 + True Peak 限幅（4× 过采样分块测量，迭代 ≤3 次）→ 结尾 3.5 s 自然衰减。

---

## 6. 版本演进（为什么有 5 个 orchestrator）

| 版本     | 目标      | 关键改动                                                                      | 客观结果                                                         |
|--------|---------|---------------------------------------------------------------------------|--------------------------------------------------------------|
| v1     | 跑通四幕骨架  | SSO 采样 + 原脚本 hybrid 层；8 段配器表；D♭ 抬升；Picardy 终止                             | 时长/LUFS/TP 达标，但频谱偏暗，主旋律被弦乐压住（lead −43.6 vs strings −35.2 dB） |
| v2     | 频谱与平衡   | presence/air EQ，lead bus +7.6 dB，strings −2.5 dB，perc +5.1 dB，弦乐 HP 80 Hz | 120–300 Hz 占比 41.9%→27.2%，主旋律抬头                              |
| v3     | 亮度与织体   | 谐波激励器；A2 圆号对位；C2 三连音固定音型；C1 小军鼓 16 分；密度 +15%                              | 5–10 kHz 0.03%→0.09%，melody −33.7 dB                         |
| v4     | 动态落差与母带 | intro 0.78、climax 1.15、−14.5 LUFS、混响 3.3 s                                | Intro→C2 落差 13.3 dB，THD 1.96%                                |
| **v5** | 最终打磨    | 旋律力度阶梯修正、激励器 −17 dB、climax 1.2、TP 改分块 4× 过采样                              | 落差 **14.3 dB**，TP **−1.02 dBTP**，与 ffmpeg 一致                 |

---

## 7. 客观验收（v5）

| 项目                  | 结果                                                                     |
|---------------------|------------------------------------------------------------------------|
| 时长                  | 240.00 s（PASS，240 ± 2）                                                 |
| Integrated loudness | −15.35 LUFS（PASS，−16…−14）                                              |
| True Peak           | −1.02 dBTP（PASS，≤ −1.0）                                                |
| Loudness Range      | 15.0 LU（电影/古典级动态，不是被压扁的 3–6 LU）                                        |
| 50–100 Hz 能量        | −48.3 dB（低音铜管/定音鼓在工作）                                                  |
| 2–5 kHz 能量          | −69.7 dB（铜管有穿透力）                                                       |
| 分轨                  | 6 条全部非空                                                                |
| MIDI                | 格式 1、6 轨、480 TPQ、239.93 s；ch0–ch4 note-on = 664 / 737 / 883 / 588 / 60 |
| ffmpeg 交叉验证         | −15.36 LUFS / −1.02 dBTP / LRA 15.00（与 `pyloudnorm` 一致）                |

各段 RMS（母带前，dBFS）：

| Intro | A1    | B     | A2    | C1    | C2        | Outro1 | Outro2 |
|-------|-------|-------|-------|-------|-----------|--------|--------|
| −36.6 | −29.8 | −34.3 | −28.3 | −24.6 | **−22.3** | −30.6  | −31.6  |

Intro → C2 落差 14.3 dB，且 B 段（−34.3）低于 A1（−29.8），形成"建立–呼吸–升级–爆发–余响"。

---

## 8. 已知约束（实测，不是理论）

1. **`pysfizz` 只能吃 ASCII 路径**：项目目录含中文，必须用 `D:\_sso` junction，见 §2.2。
2. **网络**：`raw.githubusercontent.com` 直连被重置（WinError 10054），`codeload` 整包在 348 MB 处停滞，`gh-proxy` 单连接仅
   20–60 kB/s。最终方案是 jsDelivr 的 `gcore` / `testingcf` 两条 CDN 各 1–2 并发，实测约 160 kB/s/连接。
3. **SSO 采样高频本身偏暗**：`trumpets-sus-a#4.wav` 在 5–10 kHz 仅 0.2% 能量，`horns-stc` 与 `celli-stc` 为 0%。纯 EQ
   提升只会抬噪声，因此引入谐波激励器（1.2–5 kHz 带内二次非线性 → HP 5 kHz → 按 −17 dB 相对电平叠加）。
4. **仅供学习/演示**：SSO 是 2011 年的免费库（CC Sampling Plus 1.0），即使加激励器，亮度仍达不到真正好莱坞录音水平；要"上映级"
   需换商用采样库（如 Cinesamples / Berlin 系列）。
5. **归档目录名带中文与括号**：脚本里的输出路径是 `renders/vN`，与归档目录 `renders（就是喇叭从弱到强）`
   不一致，重新渲染会新建目录而不是覆盖旧归档。

---

## 9. 许可与致谢

- 采样：**Sonatina Symphonic Orchestra**（CC Sampling Plus 1.0，v4.0，作者 Mattias Westlund，GitHub: `peastman/sso`）。
- 渲染：**sfizz / pysfizz**。
- 旋律、编曲、DSP、母带与全部代码：本项目作者。
- 研究与参数依据见 [RESEARCH_NOTES.md](RESEARCH_NOTES.md)（含 30 条史诗配乐硬规则、EQ/压缩/响度来源与自评）。
