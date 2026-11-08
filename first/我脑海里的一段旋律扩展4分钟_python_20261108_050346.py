# -*- coding: utf-8 -*-
"""
"脑海中的旋律" —— 4 分钟完整版（含弱起处理）

重要：前两个音 5（#6）是上一小节的弱起（pickup），
      小节线从 (+1) 开始，+1 对齐强拍。
      因此每段结构：
        [start-2, start)      ← pickup（2 拍，属于"上一小节"）
        [start,   start+77)   ← 主旋律（+1 在段首强拍）
        [start+77, start+96)  ← 间奏（19 拍，伴奏延续）

输出：piano_4min.wav + piano_4min.mid
"""

import numpy as np
import soundfile as sf
import struct
from scipy.signal import butter, sosfilt, fftconvolve, lfilter
from scipy.ndimage import maximum_filter1d

# ============================================================ 基础参数
SR = 44100
BPM = 192
BEAT = 60.0 / BPM
DUR = 240.0
N = int(SR * DUR)
TOTAL_BEATS = int(round(DUR / BEAT))
print(f"总拍数 {TOTAL_BEATS} @ {BPM}BPM = {DUR:.1f}s")

# ============================================================ 音高表
NAME_TO_FREQ = {
    '1': 261.63, '2': 293.66, '3': 329.63, '4': 349.23,
    '5': 392.00, '6': 440.00, '7': 493.88,
    '#2': 311.13, '#6': 466.16, '-#6': 233.08, '+1': 523.25,
}
NAME_TO_MIDI = {
    '1': 60, '2': 62, '3': 64, '4': 65, '5': 67, '6': 69, '7': 71,
    '#2': 63, '#6': 70, '-#6': 58, '+1': 72,
}

# ============================================================ 旋律拆分：pickup vs 主体
#   pickup = 上一小节的弱起（2 拍，对应 4/4 拍下的小节第 3、4 拍）
#   main   = 从 +1 开始，小节线对齐
PICKUP = [
    ('5', 1),
    ('#6', 1),
]
MAIN = [
    ('+1', 6),
    ('#6', 1), ('5', 1), ('#6', 2), ('4', 4),
    ('#2', 1), ('4', 1), ('5', 6),
    ('4', 1), ('1', 1), ('4', 2), ('1', 4),
    ('1', 1), ('2', 1), ('#2', 3), ('1', 1), ('2', 3),
    ('-#6', 1), ('1', 6),
    ('1', 1), ('2', 1), ('#2', 2), ('5', 2), ('4', 3),
    ('2', 1), ('#2', 0.5), ('2', 0.5), ('1', 6),
    ('2', 1), ('#2', 0.5), ('2', 0.5),
    ('1', 1), ('1', 2),
    ('1', 3.5, 'legato'),
    ('-#6', 0.5),
    ('1', 5, 'fade'),
]
PICKUP_LEN = sum(e[1] for e in PICKUP)  # 2 拍
MAIN_LEN = sum(e[1] for e in MAIN)  # 77 拍
print(f"pickup = {PICKUP_LEN} 拍，main = {MAIN_LEN} 拍，合计 {PICKUP_LEN + MAIN_LEN} 拍")
assert PICKUP_LEN == 2 and MAIN_LEN == 77

# 每段 96 拍 = 24 小节，8 段 = 768 拍
SEC_LEN = 96
N_SECTIONS = TOTAL_BEATS // SEC_LEN
assert N_SECTIONS * SEC_LEN == TOTAL_BEATS, f"{N_SECTIONS}×{SEC_LEN} ≠ {TOTAL_BEATS}"
INTERLUDE_LEN = SEC_LEN - MAIN_LEN  # 19 拍（[start+77, start+96)）


# ============================================================ 音频工具
def _lowpass(x, cutoff, order=2):
    sos = butter(order, cutoff, 'low', fs=SR, output='sos')
    return sosfilt(sos, x).astype(np.float32)


def _highpass(x, cutoff, order=2):
    sos = butter(order, cutoff, 'high', fs=SR, output='sos')
    return sosfilt(sos, x).astype(np.float32)


def _bandpass(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], 'band', fs=SR, output='sos')
    return sosfilt(sos, x).astype(np.float32)


# ============================================================ 合成乐器
def synth_piano(freq, dur, vel=0.6, legato=False, fade=False):
    n = int(dur * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    audio = np.zeros(n, dtype=np.float32)
    for h in range(1, 10):
        amp = 1.0 / (h ** 1.3)
        decay = np.exp(-t * (0.8 + 0.6 * h))
        audio += amp * np.sin(2 * np.pi * freq * h * t) * decay
    audio /= 3.2
    atk = int((0.04 if legato else 0.003) * SR)
    atk = min(atk, n)
    if atk > 0:
        audio[:atk] *= np.linspace(0, 1, atk)
    if fade:
        k = int(n * 0.55)
        if k > 0:
            audio[-k:] *= np.linspace(1, 0, k) ** 1.5
    return (audio * vel).astype(np.float32)


def synth_strings(freq, dur, vel=1.0, attack=0.3, release=0.5, cutoff=2800):
    n = int((dur + release) * SR)
    t = np.arange(n) / SR
    audio = np.zeros(n, dtype=np.float32)
    for det in (-0.004, 0.0, 0.004):
        phase = (freq * (1 + det) * t) % 1.0
        audio += (2 * phase - 1).astype(np.float32)
    audio /= 3
    audio = _lowpass(audio, cutoff)
    env = np.ones(n, dtype=np.float32)
    atk = int(attack * SR)
    if atk > 0:
        env[:atk] = np.linspace(0, 1, atk)
    rel = int(release * SR)
    if rel > 0:
        env[-rel:] *= np.linspace(1, 0, rel)
    return (audio * env * vel * 0.35).astype(np.float32)


def synth_bass(freq, dur, vel=1.0):
    n = int((dur + 0.2) * SR)
    t = np.arange(n) / SR
    audio = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * 2 * freq * t)
    env = np.minimum(1, t / 0.01) * np.exp(-t / (dur * 0.5 + 0.1))
    rel = np.clip((dur + 0.15 - t) / 0.15, 0, 1)
    return (audio * env * rel * vel * 0.4).astype(np.float32)


def synth_bell(freq, dur, vel=0.5):
    n = int((dur + 1.4) * SR)
    t = np.arange(n) / SR
    audio = np.zeros(n, dtype=np.float32)
    for h, amp, dec in [(1, 1.0, 1.2), (2.02, 0.4, 0.5), (3.01, 0.2, 0.3)]:
        audio += amp * np.sin(2 * np.pi * freq * h * t) * np.exp(-t / dec)
    atk = int(0.002 * SR)
    if atk > 0:
        audio[:atk] *= np.linspace(0, 1, atk)
    rel = np.clip((dur + 1.3 - t) / 1.3, 0, 1)
    return (audio * rel * vel * 0.35).astype(np.float32)


# ============================================================ 打击乐
def synth_kick(vel=0.6):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 40 + 120 * np.exp(-t / 0.03)
    phase = 2 * np.pi * np.cumsum(f) / SR
    audio = np.sin(phase) * np.exp(-t / 0.22)
    click = np.random.randn(n).astype(np.float32) * np.exp(-t / 0.004) * 0.4
    return (np.tanh(1.3 * (audio + click)) * vel).astype(np.float32)


def synth_snare(vel=0.22):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    noise = np.random.randn(n).astype(np.float32)
    body = _bandpass(noise, 800, 8000) * np.exp(-t / 0.11)
    tone = 0.35 * np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.05)
    return ((body + tone) * vel).astype(np.float32)


def synth_hat(vel=0.10, open_=False):
    n = int((0.2 if open_ else 0.04) * SR)
    t = np.arange(n) / SR
    noise = np.random.randn(n).astype(np.float32)
    audio = _highpass(noise, 7000) * np.exp(-t / (0.07 if open_ else 0.012))
    return (audio * vel).astype(np.float32)


def synth_crash(vel=0.15):
    n = int(1.8 * SR)
    t = np.arange(n) / SR
    noise = np.random.randn(n).astype(np.float32)
    return (_highpass(noise, 4000) * np.exp(-t / 0.5) * vel).astype(np.float32)


# ============================================================ 混音器
class Mixer:
    def __init__(self):
        self.buf = np.zeros((2, N), dtype=np.float32)
        self.send = np.zeros((2, N), dtype=np.float32)

    def add(self, audio, start_beat, gain=1.0, pan=0.0, send=0.0):
        i = int(round(start_beat * BEAT * SR))
        if i >= N:
            return
        if i < 0:
            audio = audio[-i:]
            i = 0
        n = min(len(audio), N - i)
        if n <= 0:
            return
        a = (pan + 1) * np.pi / 4
        lg, rg = float(np.cos(a)), float(np.sin(a))
        seg = audio[:n]
        self.buf[0, i:i + n] += seg * gain * lg
        self.buf[1, i:i + n] += seg * gain * rg
        if send:
            self.send[0, i:i + n] += seg * gain * lg * send
            self.send[1, i:i + n] += seg * gain * rg * send


# ============================================================ 旋律播放
def play_melody(mx, melody, start_beat, instrument='piano', gain=1.0,
                pan=0.0, octave=0, send=0.3, vel_scale=1.0):
    pos = 0.0
    for ev in melody:
        name = ev[0]
        dur = ev[1]
        flag = ev[2] if len(ev) > 2 else None
        freq = NAME_TO_FREQ[name] * (2.0 ** octave)
        dur_s = dur * BEAT
        if instrument == 'piano':
            tail = 0.5 if flag == 'fade' else 0.2
            audio = synth_piano(freq, dur_s + tail, vel=0.6 * vel_scale,
                                legato=(flag == 'legato'), fade=(flag == 'fade'))
        elif instrument == 'bell':
            audio = synth_bell(freq, dur_s, vel=0.55 * vel_scale)
        elif instrument == 'strings':
            audio = synth_strings(freq, dur_s, vel=0.9 * vel_scale,
                                  attack=0.15, release=0.3)
        else:
            audio = synth_piano(freq, dur_s + 0.2, vel=0.5 * vel_scale)
        mx.add(audio, start_beat + pos, gain=gain, pan=pan, send=send)
        pos += dur
    return pos


def play_section_melody(mx, start, instrument, gain, octave=0, send=0.35,
                        vel_scale=1.0, with_pickup=True):
    """渲染一段旋律：pickup（上一小节末尾）+ main（从 +1 对齐段首）。"""
    # pickup 属于"上一小节"，落在 [start-2, start)
    if with_pickup and start > 0:
        play_melody(mx, PICKUP, start - PICKUP_LEN, instrument,
                    gain=gain * 0.85, octave=octave, send=send,
                    vel_scale=vel_scale * 0.85)
    # main 从段首开始，+1 对齐强拍
    play_melody(mx, MAIN, start, instrument,
                gain=gain, octave=octave, send=send, vel_scale=vel_scale)


# ============================================================ 和弦铺底
CHORD_NOTES = [
    [60, 63, 67],  # Cm
    [58, 62, 65],  # Bb
    [63, 67, 70],  # Eb
    [55, 58, 62],  # Gm
]
CHORD_ROOTS = [48, 46, 51, 43]  # C3 Bb2 Eb3 G2


def render_pad(mx, start_beat, num_beats, gain=0.35):
    pos = 0.0
    idx = 0
    while pos < num_beats - 0.01:
        actual = min(8.0, num_beats - pos)
        chord = CHORD_NOTES[idx % 4]
        for note in chord:
            freq = 440.0 * 2 ** ((note - 69) / 12)
            audio = synth_strings(freq, actual * BEAT * 0.98, vel=1.0,
                                  attack=0.35, release=0.5)
            mx.add(audio, start_beat + pos, gain=gain, pan=0, send=0.65)
        pos += actual
        idx += 1


def render_bass(mx, start_beat, num_beats, gain=0.5):
    pos = 0.0
    idx = 0
    while pos < num_beats - 0.01:
        actual = min(8.0, num_beats - pos)
        root = CHORD_ROOTS[idx % 4]
        freq = 440.0 * 2 ** ((root - 69) / 12)
        audio = synth_bass(freq, actual * BEAT * 0.92, vel=1.0)
        mx.add(audio, start_beat + pos, gain=gain, pan=0, send=0.15)
        pos += actual
        idx += 1


def render_drums(mx, start_beat, num_beats, intensity=1.0):
    n_bars = int(num_beats // 4)
    for bar in range(n_bars):
        t0 = start_beat + bar * 4
        mx.add(synth_kick(), t0, gain=0.55 * intensity, pan=0, send=0.05)
        mx.add(synth_kick(), t0 + 2, gain=0.40 * intensity, pan=0, send=0.05)
        mx.add(synth_snare(), t0 + 1, gain=0.20 * intensity, pan=0, send=0.15)
        mx.add(synth_snare(), t0 + 3, gain=0.20 * intensity, pan=0, send=0.15)
        for k in range(8):
            open_ = (k == 7) and bar % 4 == 3
            mx.add(synth_hat(open_=open_), t0 + k * 0.5,
                   gain=0.08 * intensity, pan=0.2, send=0.05)


def render_interlude(mx, start, length=INTERLUDE_LEN, gain=0.30):
    """段末 19 拍的间奏：只延续和弦/贝斯/鼓，让旋律自然呼吸。
    pickup（下一段的弱起）会自动在最后 2 拍进入，与这里的伴奏叠加。"""
    # 和弦铺底轻轻延展（补偿：主旋律最后一个音自然 fade 到此区间）
    pass  # 伴奏已在段内铺满，这里留白呼吸


# ============================================================ 段落
def sec_intro(mx, start):
    print("  [Intro]   铺底 + 主题动机预览（+1 在结尾 2 拍前弱起进入 A1）")
    render_pad(mx, start, 96, gain=0.28)
    # intro 前面没有"上一段"，所以不渲染 pickup，只放主题动机碎片
    # 放 MAIN 的前 12 拍作为引子（弱奏、高八度铃声）
    intro_motif = MAIN[:3]  # +1（6）+ #6 + 5
    play_melody(mx, intro_motif, start + 40, 'bell', gain=0.18,
                octave=1, send=0.75, vel_scale=0.6)
    play_melody(mx, intro_motif[:1], start + 72, 'piano', gain=0.25, send=0.65)
    # 最后 2 拍：A1 的 pickup 由 sec_A1 自动渲染（在 [94, 96)）


def sec_A1(mx, start):
    print("  [A1]      钢琴主旋律（+1 对齐段首强拍，含 pickup）")
    render_pad(mx, start, 96, gain=0.28)
    render_bass(mx, start, 96, gain=0.35)
    play_section_melody(mx, start, 'piano', gain=0.85, send=0.35)
    render_interlude(mx, start)


def sec_B(mx, start):
    print("  [B]       钟琴高八度 + 轻鼓")
    render_pad(mx, start, 96, gain=0.28)
    render_bass(mx, start, 96, gain=0.40)
    play_section_melody(mx, start, 'bell', gain=0.60, octave=1, send=0.55)
    render_drums(mx, start, 96, intensity=0.5)
    render_interlude(mx, start)


def sec_A2(mx, start):
    print("  [A2]      钢琴 + 弦乐双旋律 + 中鼓")
    render_pad(mx, start, 96, gain=0.32)
    render_bass(mx, start, 96, gain=0.45)
    play_section_melody(mx, start, 'piano', gain=0.85, send=0.35)
    play_section_melody(mx, start, 'strings', gain=0.14, send=0.55,
                        with_pickup=False)  # 弦乐层不重复 pickup
    render_drums(mx, start, 96, intensity=0.7)
    render_interlude(mx, start)


def sec_C1(mx, start):
    print("  [C1]      全奏 · 高潮")
    render_pad(mx, start, 96, gain=0.34)
    render_bass(mx, start, 96, gain=0.55)
    play_section_melody(mx, start, 'piano', gain=1.0, send=0.4)
    play_section_melody(mx, start, 'strings', gain=0.20, send=0.6,
                        with_pickup=False)
    render_drums(mx, start, 96, intensity=1.0)
    render_interlude(mx, start)


def sec_C2(mx, start):
    print("  [C2]      全奏 + 钟琴叠八度")
    render_pad(mx, start, 96, gain=0.34)
    render_bass(mx, start, 96, gain=0.55)
    play_section_melody(mx, start, 'piano', gain=1.0, send=0.4)
    play_section_melody(mx, start, 'bell', gain=0.28, octave=1, send=0.55,
                        with_pickup=False)
    play_section_melody(mx, start, 'strings', gain=0.20, send=0.6,
                        with_pickup=False)
    render_drums(mx, start, 96, intensity=1.0)
    render_interlude(mx, start)


def sec_outro1(mx, start):
    print("  [Outro1]  简化 · 回钢琴")
    render_pad(mx, start, 96, gain=0.26)
    render_bass(mx, start, 96, gain=0.28)
    play_section_melody(mx, start, 'piano', gain=0.55, send=0.55)
    render_interlude(mx, start)


def sec_outro2(mx, start):
    print("  [Outro2]  碎片化 + 淡出（无下一段，不再放 pickup）")
    render_pad(mx, start, 96, gain=0.18)
    play_melody(mx, MAIN[:10], start, 'piano', gain=0.40, send=0.65)
    play_melody(mx, MAIN[:3], start + 48, 'bell', gain=0.15, octave=1, send=0.75)
    render_interlude(mx, start)


# ============================================================ 混响 / 母带
def make_ir(dur=3.5, seed=42):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    ir = np.zeros((2, n), dtype=np.float32)
    for ch in range(2):
        x = rng.standard_normal(n).astype(np.float32)
        low = _lowpass(x, 400) * np.exp(-t / 1.2)
        mid = _bandpass(x, 400, 4000) * np.exp(-t / 0.8)
        high = _highpass(x, 4000) * np.exp(-t / 0.4)
        ir[ch] = low * 1.0 + mid * 0.7 + high * 0.4
        ir[ch] *= np.minimum(1, t / 0.008)
        ir[ch] /= np.sqrt(np.sum(ir[ch] ** 2)) + 1e-9
    return ir


def apply_reverb(mx, wet_gain=0.42):
    ir = make_ir(3.5)
    wet = np.zeros_like(mx.send)
    for ch in range(2):
        wet[ch] = fftconvolve(mx.send[ch], ir[ch])[:N].astype(np.float32)
    return mx.buf + wet * wet_gain


def master(mix):
    for ch in range(2):
        mix[ch] = _highpass(mix[ch], 30)
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.85
    L = int(0.004 * SR)
    pk = maximum_filter1d(np.max(np.abs(mix), axis=0), size=2 * L + 1)
    g = np.minimum(1.0, 0.85 / (pk + 1e-9))
    a = np.exp(-1.0 / (0.08 * SR))
    gs = lfilter([1 - a], [1, -a], g)
    mix = mix * np.minimum(g, gs)
    mix = np.tanh(mix * 1.05) / 1.05
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.85
    fade_in = int(0.6 * SR)
    fade_out = int(3.5 * SR)
    mix[:, :fade_in] *= np.linspace(0, 1, fade_in)
    mix[:, -fade_out:] *= np.linspace(1, 0, fade_out)
    return mix


# ============================================================ MIDI
def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def _melody_to_events(melody, t_start, octave_off, vel):
    evs = []
    t = t_start
    for ev in melody:
        name, dur = ev[0], ev[1]
        midi = NAME_TO_MIDI[name] + octave_off * 12
        s = int(round(t * TPQ))
        e = int(round((t + dur * 0.95) * TPQ))
        evs.append((s, 1, bytes([0x90, midi, vel])))
        evs.append((e, 0, bytes([0x80, midi, 64])))
        t += dur
    return evs


TPQ = 480


def build_midi(path, bpm=BPM):
    tempo_us = int(60_000_000 / bpm)
    trk = bytearray()
    trk += vlq(0) + bytes([0xFF, 0x51, 0x03]) + tempo_us.to_bytes(3, 'big')
    trk += vlq(0) + bytes([0xC0, 0])

    abs_events = []
    # 各段主旋律（+1 在段首）+ pickup（上一段末尾）
    for sec_start, octave_off, vel in [
        (96, 0, 90),  # A1
        (192, 1, 80),  # B
        (288, 0, 95),  # A2
        (384, 0, 100),  # C1
        (480, 0, 105),  # C2
        (576, 0, 80),  # Outro1
    ]:
        # pickup 属于"上一小节" → 放在段首前 2 拍
        abs_events += _melody_to_events(PICKUP, sec_start - PICKUP_LEN, octave_off, vel - 10)
        # main 从段首开始（+1 对齐强拍）
        abs_events += _melody_to_events(MAIN, sec_start, octave_off, vel)

    # 和弦铺底
    for sec_start in [0, 96, 192, 288, 384, 480, 576, 672]:
        for bar in range(24):
            chord = CHORD_NOTES[bar % 4]
            t = sec_start + bar * 4
            for note in chord:
                s = int(round(t * TPQ))
                e = int(round((t + 3.8) * TPQ))
                abs_events.append((s, 1, bytes([0x90, note, 50])))
                abs_events.append((e, 0, bytes([0x80, note, 64])))

    abs_events.sort(key=lambda x: (x[0], x[1]))
    prev = 0
    for tick, _, data in abs_events:
        trk += vlq(tick - prev) + data
        prev = tick
    trk += vlq(0) + bytes([0xFF, 0x2F, 0x00])

    header = b'MThd' + struct.pack('>IHHH', 6, 0, 1, TPQ)
    track = b'MTrk' + struct.pack('>I', len(trk)) + bytes(trk)
    with open(path, 'wb') as f:
        f.write(header + track)


# ============================================================ 主流程
def main():
    mx = Mixer()
    sections = [
        (0, sec_intro),
        (96, sec_A1),
        (192, sec_B),
        (288, sec_A2),
        (384, sec_C1),
        (480, sec_C2),
        (576, sec_outro1),
        (672, sec_outro2),
    ]
    for start, fn in sections:
        fn(mx, start)

    print("混响 ...")
    mix = apply_reverb(mx)
    print("母带 ...")
    mix = master(mix)

    pcm = (mix.T * 32700).astype(np.int16)
    sf.write('piano_4min.wav', pcm, SR, subtype='PCM_16')
    print(f"✅ piano_4min.wav  {len(mix[0]) / SR:.2f}s")

    build_midi('piano_4min.mid')
    print("✅ piano_4min.mid")


if __name__ == '__main__':
    main()
