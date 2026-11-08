# RESEARCH_NOTES —— 好莱坞史诗交响配乐的可执行规则

> 目标文件：`旋律扩展4分钟交响版_python_20261108_f84da8.py`（原脚本，字节不变地复制为 `original_script.py`）
> 本文件只做一件事：把"为什么史诗"拆解成可以写进代码的参数与结构决策。代码是这些规则的执行器。

---

## 0. 检索方法与工具链结论（先研究，后动手）

| 结论           | 说明                                                                                                                                                | 来源                                                                                                                                                                                                                                        |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 音源用采样库而非振荡器  | SSO（Sonatina Symphonic Orchestra，CC Sampling Plus 1.0，v4.0，1.39 GB，含 Sustain/Marcato/Staccato/Legato/Tremolo 等演奏法）可直接以 SFZ 加载，正好覆盖史诗配乐的"攻击性 + 层次" | [sfzinstruments: SSO](https://sfzinstruments.github.io/orchestra/sso/) · [github.com/peastman/sso](https://github.com/peastman/sso)                                                                                                       |
| 渲染引擎用 sfizz  | `pysfizz` 是 sfizz 的 Python 绑定，`Synth.load_sfz_file()` + `render_note(pitch, vel, note_on_dur, render_dur)` 即按 MIDI 事件离屏渲染                         | 本地 `pysfizz 0.1.3`（cp314 wheel 安装成功，`import pysfizz` 通过）                                                                                                                                                                                  |
| 响度目标         | Spotify/YouTube/TIDAL/Amazon ≈ −14 LUFS，Apple Music ≈ −16 LUFS；True Peak 统一要求 < −1 dBTP（更强母带建议 −2 dBTP）                                           | [recordJet 平台规范](https://faq.recordjet.com/en/articles/6959419-how-loud-should-my-master-be-what-are-the-store-requirements) · [LUFS meter 参考](https://removevocals.ai/lufs-meter)                                                        |
| 电影/古典类节目动态范围 | "压扁"= 失去表现力；限制器只做安全网，母带增益压缩 GR ≤ 3 dB                                                                                                             | [Trailaurality: An Introduction to Epic Trailer Music Production](https://www.trailaurality.com/blog/2018/1/5/guest-post-an-introduction-to-epic-trailer-music-production)                                                                |
| 铜管 EQ 骨架     | 高通 60–80 Hz 去泥；100–200 Hz 是 boom/mud（长号尤甚）；2 kHz 附近是 presence；4–10 kHz 是 brightness，但小号极易"炸头"要控制                                                  | [How to EQ Brass](https://www.stockmusicmusician.com/blog/how-to-eq-brass) · [Brass Settings](https://m.themusictelegraph.com/584) · [EQ Cheat Sheet](https://blog.sonicbids.com/the-ultimate-eq-cheat-sheet-for-every-common-instrument) |
| 铜管压缩         | ratio 2:1–3:1、中慢 attack（过快会杀掉瞬态）、中等 release；不要过度压缩                                                                                                | [Brass Settings](https://m.themusictelegraph.com/584)                                                                                                                                                                                     |
| 侧链低频让路       | kick 触发 ducking 可让低频"泵"起来而不混浊                                                                                                                     | [brassy band 处理](https://storage.googleapis.com/klrhtbrqmqdwtkehiublog/how-to-get-rid-of-brassy-band.html)                                                                                                                                |

---

## 1. 《星球大战》主题：为什么一开场就"史诗"（10 条硬规则）

检索依据：Williams 的 Main Title 以 **B♭ 大三和弦 sforzando 全奏**开篇，紧接着是 **三支小号齐奏、位于其最辉煌的"home"音区**
的旋律；木管/弦乐 tremolo 构成上方踏板；定音鼓 + 小军鼓滚奏收束；音乐靠"同步的爆发 + 短促动机反复"制造冲击。
来源：[Analysis: Opening Logos / Star Wars](https://musicofstarwars.wordpress.com/analysis-opening-logos-star-wars/) · [Godsil 博士论文（UC Davis）: "three unison trumpets in their most brilliant possible register"](https://escholarship.org/content/qt46f2629z/qt46f2629z.pdf) · [LibreTexts: John Williams – Star Wars（曲式表: intro 铜管 fanfare → A 段小号上行跳跃旋律 → A 段变化重复）](https://human.libretexts.org/Bookshelves/Music/Resonances_-_Engaging_Music_in_its_Cultural_Context_(Morgan-Ellis_Ed.)/02:_Music_for_Storytelling/03:_Music_and_Characterization/3.02:_John_Williams_-_Star_Wars)

1. **主旋律必须"铜管化"**：旋律第一次出现就要有铜管版本，弦乐版不算史诗陈述。
2. **音区即气势**：同一旋律移到铜管最辉煌的音区（小号 F4–C5 一线），音量不变也会更"大"。
3. **主题陈述要有强度阶梯**：圆号/中低铜管 → 小号/高铜管 → 铜管齐奏，同一旋律至少三级。
4. **短动机反复**：旋律骨架用 4–5 音动机反复，便于在渐强段落"同一材料、更强配置"地重述。
5. **开篇用"突然的全奏"而不是渐入**：一个 sforzando tutti + 立即进入主题，比 8 秒淡入有效。
6. **旋律上方要有"踏板层"**：高音弦乐 tremolo 或定音鼓滚奏持续，产生悬挂感。
7. **旋律下方要有"重量层"**：低音铜管 + 定音鼓/大鼓承担低频，不要指望旋律自己变重。
8. **打击乐收束乐句**：每个大乐句结束由定音鼓 + 小军鼓滚奏"盖章"。
9. **内声部用 quartal/不协和音程**（四度堆叠）制造"军号感"，而不是纯三和弦。
10. **重复要变化伴奏**：A 段第二次出现必须换伴奏织体（而非同一条 loop 加大音量）。

## 2. 《勇闯夺命岛》/ Zimmer：为什么"有重量"（10 条硬规则）

检索依据：该片配乐被描述为"**loudly thunderous and unapologetically epic orchestra**"，开篇即"低沉的铜管 + 90
年代合成器人声垫 + 鼓击"；Zimmer 的"War"类段落靠**持续的重复音型 + 每拍不同和弦音构成**制造"mesmerising weight"
；学界把这种手法追溯到 Holst《火星》的** relentless repeating phrases + menacing percussion + militaristic brass**。
来源：[Zanobard: The Rock 配乐评述](https://zanobardreviews.com/2024/01/14/the-rock-soundtrack-review/) · [Brian Morrell《How Film & TV Music Communicate》Vol.2（"mesmerising weighty monotony countered by great harmonic colour"）](https://brianmorrell.co.uk/book2/09excitementandthegrandgesture.pdf) · [Interlude: Zimmer 与 Holst《火星》](https://interlude.hk/if-you-love-hans-zimmer-listen-to-these-7-classical-composers/)

11. **电子/合成层与管弦乐层叠加，不是二选一**：synth bass + 低音铜管同频同相位叠加，才有"混合质感"。
12. **固定音型（ostinato）是引擎**：动作段（C1/C2）必须有低音铜管的八分音符或三连音循环。
13. **低音铜管承担"重量"**：长号 + 大号 + 低音巴松在根音上做节奏型，而不是拉长音。
14. **打击乐是结构声部**：大鼓/定音鼓/小军鼓的密度变化必须与铜管力度曲线同步。
15. **重复不靠旋律靠"和声色彩"**：同一音型每拍强调不同和弦音，避免单调。
16. **低频"泵感"用侧链实现**：kick 击打瞬间让低音层轻微让路 3–6 dB。
17. **低频要"分层"而不是"堆量"**：sub（40–80 Hz）+ 低音铜管（80–200 Hz）+ 中低频弦乐（200–500 Hz）分层。
18. **段落之间要有"呼吸"**：climax 之间留 1–2 小节近乎静默，才有下一次爆发的对比。
19. **人声/合唱是"放大器"**：只在最高潮（C2）进入，混在铜管后面而不是压过铜管。
20. **电子 kick 与管弦大鼓对齐**：同一拍点，双源叠加 = 既有冲击力又有质感。

## 3. 预告片渐强结构：为什么"4 分钟不散"（10 条硬规则）

检索依据：主流做法是三/四幕（intro → build → climax →（可选第二高潮）→ outro），段落能量必须有**可辨识的边界**；Section 1
几乎不放打击乐与低频，Section 2 加入低频打击 + 节奏和弦，Section 3 全开；各幕长度大致相等，尾部约为主段的一半；"
同样内容重复两次在预告片里没有意义"。
来源：[Master The Score: How to Write Trailer Music](https://www.masterthescore.com/article/how-to-write-trailer-music-a-step-by-step-guide) · [Trailaurality（三幕 + tail 的比例与各幕特征）](https://www.trailaurality.com/blog/2018/1/5/guest-post-an-introduction-to-epic-trailer-music-production) · [Nathan Fields: 三幕结构](https://www.nathanfieldsmusic.com/blog/three-act-structure-trailer-music)

21. **一条张力曲线贯穿全曲**：建立（0–30%）→ 升级（30–55%）→ 爆发（55–85%）→ 余响（85–100%），不允许八段平均用力。
22. **每幕配器密度差 ≥ 20%**：20% → 40% → 65% → 90% → 100% → 50% → 25% → 0。
23. **"密度阶梯"用三重同步**：铜管声部数 +1、低音铜管密度 +1 层、打击乐密度 +1 层，三者同时升。
24. **低音在第一幕几乎缺席**：Intro 只留 60–80 Hz 的远处闷击，建立"压迫感"而非"热闹"。
25. **静默是乐器**：climax 前后各留一小段稀疏区（drop / stopdown）。
26. **爆发段的混响反而要更干**：C2 的 reverb wet 比 A1 低 20–30%，否则高频被吃掉、冲击力消失。
27. **每 4 小节必须有新信息**：换织体、换铜管组、换打击乐型，不做"整体 +6dB"式的假渐强。
28. **结尾要有"终止一击 + 余响"**：一记全奏和弦（Picardy third）后进入 3–4 秒自然衰减。
29. **半音和声挤压**：爆发前插入 ♭II（那不勒斯）大三和弦，再解决回主和弦，制造"抬升"。
30. **同一条主旋律必须由不同铜管组承担**（A1 圆号 / A2 小号 / C1 铜管齐奏 / C2 全铜管 + 合唱）。

---

## 4. 和声与终止式（本曲具体决策）

| 决策                                         | 依据                                                                                                                                                                                                                                                                                                                                         |
|--------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 主调 C 和声小调（保留原脚本）                           | 原作素材                                                                                                                                                                                                                                                                                                                                       |
| 最终全奏最后一小节改为 **C 大三和弦（Picardy third）**      | "minor key piece ends on major tonic chord… 传递 hope/triumph/relief"：[The Music Theory Professor](https://www.themusictheoryprofessor.com/article/how-the-picardy-third-enhances-the-expressiveness-of-a-musical-piece/) · [Beat Kitchen](https://beatkitchen.io/guides/musician-basics/07-the-four-chord-progression-and-borrowed-chords/) |
| C2 爆发前插入 **D♭ 大三和弦（♭II / Neapolitan）** 两小节 | "Neapolitan：poignant, dramatic / yearning pull toward V"：[Modal Interchange 指南](https://www.piano-composer-teacher-london.co.uk/post/how-to-use-modal-interchange-a-composers-guide) · [13 Songwriting Tricks](https://www.fachords.com/songwriting-tricks/)                                                                               |
| 低音铜管固定音型（八分音符根音，第 4 拍换五度/七度）               | Zimmer "weight" 手法，见 §2 规则 12–13                                                                                                                                                                                                                                                                                                           |

## 5. 频谱与混音的具体参数（写进代码的数值）

| Bus                    | 处理                                                                                                                                                     | 数值                |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|
| brass（小号/圆号/长号中高）      | HP 80 Hz（18 dB/oct）+ 200–400 Hz −1.5 dB（窄带，去"盒音"）+ 2–5 kHz +1 dB（光泽）+ 胶水压缩 2:1 / attack 30 ms / release 250 ms / GR 1–2 dB                             | 依据 §0 铜管 EQ 与压缩条目 |
| low（长号/大号/低音弦乐/合成 sub） | **不 HP**（保 40–100 Hz），kick 侧链 ducking：threshold −18 dB、ratio 3:1、attack 5 ms、release 120 ms                                                            | §2 规则 16          |
| perc                   | 定音鼓保 60–100 Hz 基频，300–500 Hz −2 dB（避开铜管中低）；小军鼓 HP 200 Hz，保 3–6 kHz 脆度                                                                                  | sonicbids 频段表     |
| reverb                 | 铜管 send：大厅/板式混合 2.8–3.2 s；打击乐 send：1.2–1.6 s；C2 wet 比 A1 低 25%                                                                                         | §3 规则 26          |
| master                 | ① 20 Hz HP（24 dB/oct）② 胶水压缩 1.8:1 / 35 ms / 250 ms / GR ≤ 3 dB ③ 轻饱和 tanh（THD ≈ 1–2%）④ True Peak 限幅 −1.0 dBTP ⑤ 目标 −15 LUFS（区间 −16…−14）⑥ 结尾 3.5 s fade | §0 响度条目           |

---

## 6. 工程实现中的三个真实约束（不是理论，是实测）

### 6.1 网络：GitHub 直连/代理被限速

- `raw.githubusercontent.com` 直连被重置（WinError 10054）；`codeload.github.com` 可连但整包 1.4 GB 在 348 MB 处停滞。
- `gh-proxy.com` / `ghproxy.net` 单连接 20–60 kB/s，且并发一高就集体超时。
- **最终可用方案**：jsDelivr 的 `gcore.jsdelivr.net` / `testingcf.jsdelivr.net` 镜像
  （`https://gcore.jsdelivr.net/gh/peastman/sso@master/<path>`），2 条 CDN 各 1 并发，
  实测 ~160 kB/s/连接，20 分钟拿完 300 MB 采样。
- 只下载 `epic_engine.INST` 真正会用到的音色所在的采样（550 个文件），而不是整包 728 个。
- 记录：`tools_fetch_subset.py`（抓 SFZ 文本）、`tools_fetch_samples.py`（抓采样，多 CDN 轮换 + Range 续传）。

### 6.2 pysfizz 只能吃 ASCII 路径

- 项目目录含中文，`Synth.load_sfz_file()` 抛
  `No mapping for the Unicode character exists in the target multi-byte code page`。
- 解决：建立 ASCII junction `D:\_sso` → 采样库，`epic_engine.SSO_ROOT` 自动优先使用它。

### 6.3 SSO 采样在高频几乎没有能量（实测，决定了混音策略）

| 素材                        | 20–300 Hz | 0.5–1.2k | 2.5–5k | 5–10k    |
|---------------------------|-----------|----------|--------|----------|
| `trumpets-sus-a#4.wav`    | 0%        | 23.7%    | 4.9%   | **0.2%** |
| `horns-stc-rr1-a#3.wav`   | 8.1%      | 7.1%     | 0.1%   | **0%**   |
| `celli-stc-rr1-a2.wav`    | 20.4%     | 7.8%     | 0.1%   | **0%**   |
| 原始渲染的 trumpet 单音（pysfizz） | 0%        | 23.4%    | 13.4%  | **0.2%** |

结论：**这不是渲染链把高频吃掉了，是库本身偏暗**。纯 EQ 提升只会抬噪声，
所以引入**谐波激励器**（`exciter()`：1.2–5 kHz 带内做二次非线性，再高通 5 kHz，
按 −17 dB 相对电平叠加）——这正是商业 exciter 的原理，用真实演奏材料生成 5–10 kHz 的"金属光泽"。

---

## 7. 交付自评（客观 + 主观）

### 7.1 客观验收（v5，最终交付）

| 项目                  | 结果                                                                                  |
|---------------------|-------------------------------------------------------------------------------------|
| 时长                  | 240.00 s（PASS，240 ± 2）                                                              |
| Integrated loudness | −15.35 LUFS（PASS，−16…−14）                                                           |
| True Peak           | −1.02 dBTP（PASS，≤ −1.0）                                                             |
| Loudness Range      | 15.0 LU（电影/古典级动态，不是压扁的 3–6 LU）                                                      |
| 50–100 Hz 能量        | −47.3 dB（PASS，低音铜管/定音鼓在工作）                                                          |
| 2–5 kHz 能量          | −70.1 dB（PASS，铜管有穿透力）                                                               |
| 分轨                  | 6 条（brass / low_brass_bass / strings / percussion / choir_hybrid / melody_lead）全部非空 |
| MIDI                | 格式 1、6 轨、480 TPQ、239.93 s，ch0–ch4 分别为 664/737/883/588/60 个 note-on                  |
| ffmpeg 交叉验证         | −15.36 LUFS / −1.02 dBTP / LRA 15.0（与 pyloudnorm 一致）                                |

各段 RMS（母带前，dBFS）：

| Intro | A1    | B     | A2    | C1    | C2        | Outro1 | Outro2 |
|-------|-------|-------|-------|-------|-----------|--------|--------|
| −36.6 | −29.8 | −34.3 | −28.3 | −24.6 | **−22.3** | −30.6  | −31.6  |

Intro → C2 落差 **14.3 dB**，且 B 段（−34.3）低于 A1（−29.8），形成"建立–呼吸–升级–爆发–余响"。

### 7.2 主观自评（对照任务书 §7 的四个问题）

1. **C2 是否比 A1 更"厚"？** 是。铜管声部：A1 = 圆号独奏 + 低音铜管长音（2 个铜管组）→ C2 = 小号 + 圆号 + 长号 + 大号 +
   全铜管叠置（5 个铜管组 + 合唱 + 木管高八度）。
   低音铜管：A1 在根音上做长音 → A2 起改为八分音符固定音型，C2 再加一轨三连音（v3 起）。
   打击乐：A1 每小节 1 记定音鼓 + 隔小节弱击小军鼓 → C1 每小节定音鼓 + 大鼓 + 小军鼓 + 吊钹 → C2 加电子 kick 与 8
   分音符小军鼓，密度约为 A1 的 4 倍。
   客观佐证：percussion 分轨 C2 = −27.4 dB，A1 = −49.3 dB（+21.9 dB）。
2. **主旋律是否"圆号 → 小号 → 铜管齐奏 → 全铜管+合唱"？** 是，且每一级都可测：
   melody_lead 分轨：A1 −30.9 dB（圆号独奏）→ A2 −30.3 dB（小号独奏 + 圆号助奏）→ C1 −29.5 dB（小号组齐奏）→ C2 −28.4
   dB（小号+圆号+长号八度齐奏 + 唱诗班）。
3. **结尾是否有清晰的 Picardy third 终止一击？** 有。Outro2 第 18–19 小节先走 V（G 大三和弦，两段力度递进 78→96），第 20
   小节（235.0 s）全铜管 C **大**三和弦齐奏（36…79 十个音）+ 大鼓 + 吊钹 + 定音鼓 + 钟琴，随后 3.5 s 自然衰减，没有任何硬切。
4. **拿掉画面能不能听出"英雄集结/太空歌剧"？** 结构上成立：主题四次陈述逐级加码、♭II（D♭）抬升后砸进爆发、爆发段混响比 A1 干
   28%、终止用皮卡迪三度。**局限**：SSO 是 2011 年的免费库，高频本身不足（5 kHz 以上仅
   0.4%），即使加了激励器，亮度仍达不到真正好莱坞录音的水平；如果要"上映级"，必须换商用库（如 Cinesamples/Berlin 系列），这超出"
   免费可复现"的约束。

### 7.3 5 个版本各自解决了什么

| 版本 | 目标      | 关键改动                                                               | 客观结果                                                      |
|----|---------|--------------------------------------------------------------------|-----------------------------------------------------------|
| v1 | 跑通四幕骨架  | SSO 采样 + 原脚本 hybrid 层；四幕配器表；Db 抬升；Picardy                          | 时长/LUFS/TP 达标，但频谱偏暗、主旋律被弦乐压住（lead −43.6 vs strings −35.2） |
| v2 | 频谱与平衡   | presence/air EQ、lead +7.6 dB、strings −2.5 dB、perc +5.1 dB、弦乐 HP 80 | 120–300 Hz 占比 41.9%→27.2%，主旋律抬头                           |
| v3 | 亮度与织体   | 谐波激励器、A2 圆号对位、C2 三连音固定音型、C1 小军鼓 16 分、密度 +15%                       | 5–10 kHz 0.03%→0.09%，melody −33.7 dB                      |
| v4 | 动态落差与母带 | intro 0.78、climax 1.15、−14.5 LUFS、混响 3.3 s                         | Intro→C2 落差 13.3 dB，THD 1.96%                             |
| v5 | 最终打磨    | 旋律力度阶梯修正、exciter −17 dB、climax 1.2、TP 测量改为分块 4× 过采样                | 落差 14.3 dB，TP −1.02 dBTP，与 ffmpeg 一致                      |

