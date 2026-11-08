# =============================================================================
# 钢琴旋律生成 —— 从"脑海中的一段简谱"到 WAV / MIDI
# =============================================================================
#
# 比如说我脑海里的一段旋律：
#
#   5（#6）（+1）-----（#6）5（#6）-4---（#2）45-----414-1---12（#2）--12--
#   （-#6）1-----12（#2）-5-4--2【（#2）2】1-----2【（#2）2】11-{1--【-】}
#   【（-#6）】1————>
#
# 注释： 【里面是原速两倍】   {只有这里面的音是连的}
#
# -----------------------------------------------------------------------------
# 简谱记号约定（本脚本的解析规则）：
#   - 数字 1~7              = 基本音级（1 = C4）
#   - ( ) 只是把变音记号括起来，本身不算时长，例如 （#6）= 升6，（-#6）= 低八度升6
#   - +1 / -#6 前的 + / -   = 高 / 低八度（+1 = 高八度1，-#6 = 低八度升6）
#   - 数字后面的 -          = 延长 1 拍（"-----" = 延长 5 拍）
#   - 【 】里的内容          = 时值减半（原速两倍）
#   - { }  里的内容          = 连奏（legato），音与音之间不断开
#   - ————> 结尾            = 长音渐弱收尾
#   - 全曲整体速度          = BPM 192（相对原谱 96 快一倍）
# =============================================================================

import numpy as np
import soundfile as sf
import struct

SR = 44100
BPM = 192  # 整体速度快一倍
BEAT = 60.0 / BPM

# ---------- 音高表 ----------
FREQ = {
    '1': 261.63, '2': 293.66, '3': 329.63, '4': 349.23,
    '5': 392.00, '6': 440.00, '7': 493.88,
    '#2': 311.13, '#6': 466.16,
    '+1': 523.25, '-#6': 233.08,
}
MIDI = {
    '1': 60, '2': 62, '3': 64, '4': 65, '5': 67, '6': 69, '7': 71,
    '#2': 63, '#6': 70, '+1': 72, '-#6': 58,
}

# ---------- 谱子展开（上面的旋律逐音展开成 (音名, 拍数[, 标记])） ----------
# 标记 flag: 'fade' = 渐弱收尾, 'legato' = 连奏
events = [
    # 5（#6）（+1）-----
    ('5', 1), ('#6', 1), ('+1', 6),
    # （#6）5（#6）-4---
    ('#6', 1), ('5', 1), ('#6', 2), ('4', 4),
    # （#2）45-----
    ('#2', 1), ('4', 1), ('5', 6),
    # 414-1---
    ('4', 1), ('1', 1), ('4', 2), ('1', 4),
    # 12（#2）--12--
    ('1', 1), ('2', 1), ('#2', 3), ('1', 1), ('2', 3),
    # （-#6）1-----
    ('-#6', 1), ('1', 6),
    # 12（#2）-5-4--
    ('1', 1), ('2', 1), ('#2', 2), ('5', 2), ('4', 3),
    # 2【（#2）2】1-----
    ('2', 1), ('#2', 0.5), ('2', 0.5), ('1', 6),
    # 2【（#2）2】
    ('2', 1), ('#2', 0.5), ('2', 0.5),
    # 11-
    ('1', 1), ('1', 2),
    # {1--【-】}  ← 连奏组：1 + 2 + 0.5 = 3.5 拍，内部连续
    ('1', 3.5, 'legato'),
    # 【（-#6）】  ← 原速两倍 = 0.5 拍
    ('-#6', 0.5),
    # 1————>   ← 5 拍长音，渐弱收尾
    ('1', 5, 'fade'),
]


# ---------- 类钢琴合成 ----------
def synth_piano(freq, duration, velocity=0.6, fade=False, legato=False):
    n = int(duration * SR)
    if n <= 0:
        return np.zeros(0)
    t = np.arange(n) / SR
    audio = np.zeros(n)
    for h in range(1, 10):  # 谐波叠加
        amp = 1.0 / (h ** 1.3)
        decay = np.exp(-t * (0.8 + 0.6 * h))  # 高次谐波衰减更快
        audio += amp * np.sin(2 * np.pi * freq * h * t) * decay
    # 起音：连奏音用更缓的 attack（听起来像从前一个音延续过来）
    atk = int((0.04 if legato else 0.003) * SR)
    atk = min(atk, n)
    if atk > 0:
        audio[:atk] *= np.linspace(0, 1, atk)
    if fade:  # 尾部渐弱（对应 ————>）
        tail = np.ones(n)
        k = int(n * 0.55)
        tail[-k:] = np.linspace(1, 0, k) ** 1.5
        audio *= tail
    return audio * velocity


def add_reverb(audio, delay=0.06, decay=0.35, n=4):
    d = int(delay * SR)
    out = np.zeros(len(audio) + d * n)
    out[:len(audio)] += audio
    for i in range(1, n + 1):
        out[i * d:i * d + len(audio)] += audio * (decay ** i)
    return out


# ---------- 渲染 WAV ----------
total_beats = sum(e[1] for e in events)
total_samples = int(total_beats * BEAT * SR) + SR
mix = np.zeros(total_samples)
pos = 0.0
for ev in events:
    name, dur = ev[0], ev[1]
    flag = ev[2] if len(ev) > 2 else None
    fade = flag == 'fade'
    legato = flag == 'legato'
    start = int(pos * BEAT * SR)
    tail_extra = 0.50 if fade else 0.20  # 渐弱音多留一点尾巴
    note = synth_piano(FREQ[name], dur * BEAT + tail_extra, fade=fade, legato=legato)
    end = min(start + len(note), total_samples)
    mix[start:end] += note[:end - start]
    pos += dur

mix = add_reverb(mix)
mix = mix / np.max(np.abs(mix)) * 0.85
sf.write('piano.wav', mix, SR)
print(f'✅ piano.wav  时长约 {len(mix) / SR:.2f}s  共 {total_beats} 拍 @ {BPM}BPM')


# ---------- 纯 Python 生成 MIDI（无需第三方库） ----------
def vlq(n):
    """MIDI Variable-Length Quantity 编码"""
    out = [n & 0x7F];
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80);
        n >>= 7
    return bytes(reversed(out))


def build_midi(events, bpm, path, tpq=480, program=0):
    tempo_us = int(60_000_000 / bpm)
    trk = bytearray()
    # Tempo meta
    trk += vlq(0) + bytes([0xFF, 0x51, 0x03]) + tempo_us.to_bytes(3, 'big')
    # Program change（0 = Acoustic Grand Piano）
    trk += vlq(0) + bytes([0xC0, program])

    abs_events = []
    t = 0.0
    for ev in events:
        name, dur = ev[0], ev[1]
        flag = ev[2] if len(ev) > 2 else None
        fade = flag == 'fade'
        legato = flag == 'legato'
        key = MIDI[name]
        s = int(round(t * tpq))
        e = int(round((t + dur) * tpq))
        if legato:
            # 连奏：note on 提前一点点，与前一个音轻微重叠 → 产生 legato 效果
            s2 = max(0, s - int(tpq * 0.05))
            abs_events.append((s2, 1, bytes([0x90, key, 90])))
            abs_events.append((e, 0, bytes([0x80, key, 64])))
        else:
            abs_events.append((s, 1, bytes([0x90, key, 90])))
            abs_events.append((e, 0, bytes([0x80, key, 64])))
        if fade:
            # 渐弱（>）：用 CC11 Expression 分 8 段从 110 降到 0
            steps = 8
            for i in range(steps + 1):
                tick = int(s + (e - s) * i / steps)
                val = int(110 * (1 - i / steps))
                abs_events.append((tick, 2, bytes([0xB0, 11, val])))
        t += dur

    abs_events.sort(key=lambda x: (x[0], x[1]))  # 同一 tick 先 off 后 on
    prev = 0
    for tick, _, data in abs_events:
        trk += vlq(tick - prev) + data
        prev = tick
    trk += vlq(0) + bytes([0xFF, 0x2F, 0x00])  # End of track

    header = b'MThd' + struct.pack('>IHHH', 6, 0, 1, tpq)
    track = b'MTrk' + struct.pack('>I', len(trk)) + bytes(trk)
    with open(path, 'wb') as f:
        f.write(header + track)


build_midi(events, BPM, 'piano.mid')
print('✅ piano.mid  已生成（BPM =', BPM, '，双击即可播放）')
