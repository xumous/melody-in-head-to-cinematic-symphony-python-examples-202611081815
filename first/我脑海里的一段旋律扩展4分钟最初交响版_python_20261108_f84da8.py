# -*- coding: utf-8 -*-
"""
"脑海中的旋律" —— 4 分钟电影配乐交响乐版（B 段全程长笛）

修改记录：
  v1: sec_B 长笛→双簧管切换时从 MAIN[0] 重开，1:15 旋律错位
  v2: sec_B 补 pickup，解决 1:00 缺前两音；重写 synth_oboe 保留基频
  v3: sec_outro2 补 pickup + 修时序，解决 3:30 之后的同类问题
  v4: sec_B 尝试 dovetail 交叠过渡，但仍感觉 1:15 音色变化
  v5: (本版) sec_B 全程使用长笛，不切换音色
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

# ============================================================ 音高 & 旋律
NAME_TO_FREQ = {
    '1': 261.63, '2': 293.66, '3': 329.63, '4': 349.23,
    '5': 392.00, '6': 440.00, '7': 493.88,
    '#2': 311.13, '#6': 466.16, '-#6': 233.08, '+1': 523.25,
}
NAME_TO_MIDI = {
    '1': 60, '2': 62, '3': 64, '4': 65, '5': 67, '6': 69, '7': 71,
    '#2': 63, '#6': 70, '-#6': 58, '+1': 72,
}

PICKUP = [('5', 1), ('#6', 1)]
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
PICKUP_LEN = sum(e[1] for e in PICKUP)
MAIN_LEN = sum(e[1] for e in MAIN)
assert PICKUP_LEN == 2 and MAIN_LEN == 77

SEC_LEN = 96
assert TOTAL_BEATS // SEC_LEN == 8

# ============================================================ 和声（C 和声小调）
CHORD_LIB = {
    'Cm': [60, 63, 67],
    'Ab': [56, 60, 63],
    'Fm': [53, 56, 60],
    'G': [55, 59, 62],
}
CHORD_BASS_MIDI = {'Cm': 36, 'Ab': 32, 'Fm': 29, 'G': 31}
CHORD_PROG_12 = ['Cm', 'Ab', 'Fm', 'G'] * 3


def midi_to_freq(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ============================================================ 滤波器 / 包络
def _lowpass(x, cutoff, order=2):
    cutoff = min(max(cutoff, 20), SR * 0.45)
    return sosfilt(butter(order, cutoff, 'low', fs=SR, output='sos'), x).astype(np.float32)


def _highpass(x, cutoff, order=2):
    cutoff = min(max(cutoff, 20), SR * 0.45)
    return sosfilt(butter(order, cutoff, 'high', fs=SR, output='sos'), x).astype(np.float32)


def _bandpass(x, lo, hi, order=2):
    lo = max(lo, 20);
    hi = min(hi, SR * 0.45)
    if hi <= lo:
        return np.zeros_like(x, dtype=np.float32)
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x).astype(np.float32)


def _env(n, attack=0.05, release=0.2):
    env = np.ones(n, dtype=np.float32)
    a = min(int(attack * SR), n)
    if a > 0:
        env[:a] = np.linspace(0, 1, a) ** 0.7
    r = min(int(release * SR), n)
    if r > 0:
        env[-r:] *= np.linspace(1, 0, r) ** 0.7
    return env


# ============================================================ 合成乐器
def synth_strings(freq, dur_s, vel=1.0, attack=0.08, release=0.25,
                  detune=(-0.006, 0, 0.006), vibrato=0.003, cutoff=3500):
    n = int((dur_s + release) * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    audio = np.zeros(n, dtype=np.float32)
    for det in detune:
        inst = freq * (1 + det) * (1 + vibrato * np.sin(2 * np.pi * 5.5 * t))
        phase = np.cumsum(inst) / SR
        audio += (2 * (phase % 1.0) - 1).astype(np.float32)
    audio /= len(detune)
    audio = _lowpass(audio, cutoff * (0.55 + 0.45 * vel))
    return (audio * _env(n, attack, release) * vel * 0.16).astype(np.float32)


def synth_brass(freq, dur_s, vel=1.0, attack=0.04, release=0.12, bright=1.0):
    n = int((dur_s + release) * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    audio = np.zeros(n, dtype=np.float32)
    for det in (-0.004, 0, 0.004):
        phase = np.cumsum(np.full(n, freq * (1 + det))) / SR
        audio += (2 * (phase % 1.0) - 1).astype(np.float32)
    audio /= 3.0
    audio = _lowpass(audio, 4200 * bright)
    audio = np.tanh(audio * (1.2 + vel * 0.8))
    return (audio * _env(n, attack, release) * vel * 0.15).astype(np.float32)


def synth_flute(freq, dur_s, vel=1.0, attack=0.05, release=0.15):
    n = int((dur_s + release) * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    inst = freq * (1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.4))
    phase = np.cumsum(inst) / SR
    audio = np.sin(2 * np.pi * phase) + 0.3 * np.sin(4 * np.pi * phase) + 0.1 * np.sin(6 * np.pi * phase)
    breath = np.random.randn(n).astype(np.float32) * 0.06
    audio = _lowpass(audio + breath, 5500)
    return (audio * _env(n, attack, release) * vel * 0.22).astype(np.float32)


def synth_oboe(freq, dur_s, vel=1.0, attack=0.05, release=0.15):
    n = int((dur_s + release) * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    inst = freq * (1 + 0.004 * np.sin(2 * np.pi * 5.4 * t))
    phase = np.cumsum(inst) / SR
    y = (2 * (phase % 1.0) - 1).astype(np.float32)
    body = _lowpass(y, max(freq * 3.5, 800))
    nasal = _bandpass(y, 1200, 2400) * 0.45
    out = body + nasal
    return (out * _env(n, attack, release) * vel * 0.22).astype(np.float32)


def synth_violin(freq, dur_s, vel=1.0, attack=0.06, release=0.22):
    return synth_strings(freq, dur_s, vel=vel, attack=attack, release=release,
                         detune=(-0.003, 0, 0.003), vibrato=0.005, cutoff=4200)


def synth_bass_inst(freq, dur_s, vel=1.0):
    n = int((dur_s + 0.15) * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    audio = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.1 * np.sin(6 * np.pi * freq * t)
    bow = _bandpass(np.random.randn(n).astype(np.float32), 100, 800) * 0.08
    audio = (audio + bow).astype(np.float32)
    return (audio * _env(n, 0.06, 0.15) * vel * 0.22).astype(np.float32)


def synth_harp(freq, dur_s, vel=1.0, tail=1.5):
    n = int((dur_s + tail) * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    audio = np.zeros(n, dtype=np.float32)
    for h, a in [(1, 1.0), (2, 0.5), (3, 0.25), (4, 0.12), (5, 0.06)]:
        tau = tail / (h ** 0.6)
        audio += a * np.sin(2 * np.pi * freq * h * t) * np.exp(-t / tau)
    return (audio * _env(n, 0.003, tail) * vel * 0.15).astype(np.float32)


def synth_choir(freq, dur_s, vel=1.0, attack=0.4, release=0.5):
    n = int((dur_s + release) * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    audio = np.zeros(n, dtype=np.float32)
    for det in (-0.005, 0, 0.005):
        inst = freq * (1 + det) * (1 + 0.003 * np.sin(2 * np.pi * 5.0 * t))
        phase = np.cumsum(inst) / SR
        audio += (2 * (phase % 1.0) - 1).astype(np.float32)
    audio /= 3.0
    out = np.zeros(n, dtype=np.float32)
    for fc, bw, amp in [(750, 250, 1.0), (1150, 300, 0.5), (2600, 500, 0.2)]:
        out += amp * _bandpass(audio, fc - bw / 2, fc + bw / 2)
    return (out * _env(n, attack, release) * vel * 0.13).astype(np.float32)


def synth_piano(freq, dur_s, vel=0.6, legato=False, fade=False):
    n = int(dur_s * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    audio = np.zeros(n, dtype=np.float32)
    for h in range(1, 9):
        audio += (1.0 / (h ** 1.3)) * np.sin(2 * np.pi * freq * h * t) * np.exp(-t * (0.8 + 0.6 * h))
    audio /= 3.0
    atk = min(int((0.04 if legato else 0.003) * SR), n)
    if atk > 0:
        audio[:atk] *= np.linspace(0, 1, atk)
    if fade:
        k = int(n * 0.55)
        if k > 0:
            audio[-k:] *= np.linspace(1, 0, k) ** 1.5
    return (audio * vel).astype(np.float32)


# ----------------------------------------------------------- 打击乐
def synth_timpani(vel=1.0, pitch=1.0):
    n = int(1.5 * SR)
    t = np.arange(n) / SR
    f = (60 + 40 * np.exp(-t / 0.08)) * pitch
    phase = 2 * np.pi * np.cumsum(f) / SR
    audio = np.sin(phase) * np.exp(-t / 0.6) + 0.4 * np.sin(1.5 * phase) * np.exp(-t / 0.3)
    click = np.random.randn(n).astype(np.float32) * np.exp(-t / 0.01) * 0.4
    return (np.tanh((audio + click) * 1.2) * vel * 0.4).astype(np.float32)


def synth_bass_drum(vel=1.0):
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    f = 38 + 30 * np.exp(-t / 0.1)
    phase = 2 * np.pi * np.cumsum(f) / SR
    audio = np.sin(phase) * np.exp(-t / 0.5)
    click = np.random.randn(n).astype(np.float32) * np.exp(-t / 0.005) * 0.3
    return (np.tanh(audio + click) * vel * 0.55).astype(np.float32)


def synth_crash(vel=1.0, dur_s=2.5):
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    audio = _highpass(np.random.randn(n).astype(np.float32), 3500) * np.exp(-t / 0.9)
    for r in (1.0, 1.7, 2.4, 3.1, 4.5):
        audio += (0.04 * np.sin(2 * np.pi * 380 * r * t) * np.exp(-t / 0.35)).astype(np.float32)
    return (audio * vel * 0.22).astype(np.float32)


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
            audio = audio[-i:];
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
def play_note(mx, ev, beat_pos, instrument, gain=1.0, octave=0, send=0.4, vel=1.0):
    name, dur = ev[0], ev[1]
    flag = ev[2] if len(ev) > 2 else None
    freq = NAME_TO_FREQ[name] * (2 ** octave)
    dur_s = dur * BEAT

    if instrument == 'strings':
        audio = synth_strings(freq, dur_s * 0.95, vel=vel, attack=0.06, release=0.2)
    elif instrument == 'violin':
        audio = synth_violin(freq, dur_s * 0.95, vel=vel)
    elif instrument == 'horn':
        audio = synth_brass(freq, dur_s * 0.95, vel=vel, attack=0.06, release=0.12, bright=0.9)
    elif instrument == 'trumpet':
        audio = synth_brass(freq, dur_s * 0.9, vel=vel, attack=0.03, release=0.1, bright=1.4)
    elif instrument == 'trombone':
        audio = synth_brass(freq / 2, dur_s * 0.95, vel=vel, attack=0.05, release=0.12, bright=1.0)
    elif instrument == 'flute':
        audio = synth_flute(freq, dur_s * 0.9, vel=vel)
    elif instrument == 'oboe':
        audio = synth_oboe(freq, dur_s * 0.9, vel=vel)
    elif instrument == 'choir':
        audio = synth_choir(freq, dur_s * 0.9, vel=vel)
    elif instrument == 'piano':
        audio = synth_piano(freq, dur_s + 0.2, vel=0.6 * vel,
                            legato=(flag == 'legato'), fade=(flag == 'fade'))
    else:
        audio = synth_strings(freq, dur_s * 0.95, vel=vel)

    mx.add(audio, beat_pos, gain=gain, pan=0, send=send)


def play_main(mx, start, instrument, gain, octave=0, send=0.4, vel=1.0,
              with_pickup=True):
    if with_pickup and start > 0:
        pos = -PICKUP_LEN
        for ev in PICKUP:
            play_note(mx, ev, start + pos, instrument, gain * 0.9, octave, send, vel * 0.85)
            pos += ev[1]
    pos = 0
    for ev in MAIN:
        play_note(mx, ev, start + pos, instrument, gain, octave, send, vel)
        pos += ev[1]


def _play_melody_events(mx, melody, start_beat, instrument, gain=1.0,
                        octave=0, send=0.4, vel=1.0):
    pos = 0.0
    for ev in melody:
        play_note(mx, ev, start_beat + pos, instrument, gain, octave, send, vel)
        pos += ev[1]
    return pos


# ============================================================ 编曲层
def render_strings_pad(mx, start, num_beats, gain=0.45, vel=0.85,
                       attack=0.15, cutoff=3500):
    pos, idx = 0, 0
    while pos < num_beats - 0.01:
        dur = min(8.0, num_beats - pos)
        notes = CHORD_LIB[CHORD_PROG_12[idx % 12]]
        for k, m in enumerate([notes[0] - 12, notes[1] - 12, notes[0], notes[1], notes[2]]):
            audio = synth_strings(midi_to_freq(m), dur * BEAT * 0.95, vel=vel,
                                  attack=attack, release=0.3, cutoff=cutoff)
            mx.add(audio, start + pos, gain=gain, pan=(k - 2) * 0.2, send=0.55)
        pos += dur;
        idx += 1


def render_bass(mx, start, num_beats, gain=0.55, vel=0.85):
    pos, idx = 0, 0
    while pos < num_beats - 0.01:
        dur = min(8.0, num_beats - pos)
        bass = CHORD_BASS_MIDI[CHORD_PROG_12[idx % 12]]
        audio = synth_bass_inst(midi_to_freq(bass), dur * BEAT * 0.92, vel=vel)
        mx.add(audio, start + pos, gain=gain, pan=0, send=0.2)
        if vel >= 0.9:
            for k in range(1, int(dur * 2), 2):
                audio2 = synth_bass_inst(midi_to_freq(bass + 7), BEAT * 0.4, vel=vel * 0.6)
                mx.add(audio2, start + pos + k * 0.5, gain=gain * 0.6, pan=0, send=0.15)
        pos += dur;
        idx += 1


def render_harp(mx, start, num_beats, gain=0.22, vel=0.8):
    pos, idx = 0, 0
    while pos < num_beats - 0.01:
        dur = min(8.0, num_beats - pos)
        notes = CHORD_LIB[CHORD_PROG_12[idx % 12]]
        arp = [notes[0] - 12, notes[1] - 12, notes[2] - 12, notes[0], notes[1],
               notes[2], notes[0] + 12, notes[1] + 12]
        for k, m in enumerate(arp):
            if pos + k >= num_beats:
                break
            audio = synth_harp(midi_to_freq(m), 0.5, vel=vel * 0.7)
            mx.add(audio, start + pos + k, gain=gain, pan=0.3, send=0.6)
        pos += dur;
        idx += 1


def render_timpani(mx, start, num_beats, gain=0.45, pattern='light', vel=0.85):
    n_bars = int(num_beats // 4)
    pitch_map = {'Cm': 1.0, 'Ab': 0.84, 'Fm': 0.75, 'G': 0.79}
    for bar in range(n_bars):
        t0 = start + bar * 4
        chord_name = CHORD_PROG_12[(bar // 2) % 12]
        p = pitch_map.get(chord_name, 1.0)
        if pattern == 'light':
            mx.add(synth_timpani(vel * 0.6, p), t0, gain=gain, pan=-0.2, send=0.3)
        elif pattern == 'heavy':
            mx.add(synth_timpani(vel * 1.0, p), t0, gain=gain, pan=-0.2, send=0.3)
            mx.add(synth_timpani(vel * 0.6, p), t0 + 2, gain=gain * 0.7, pan=-0.2, send=0.3)
        elif pattern == 'roll':
            for k in range(16):
                intensity = 0.15 + 0.7 * (k / 16.0)
                mx.add(synth_timpani(intensity * vel, p), t0 + k * 0.25,
                       gain=gain * 0.55, pan=-0.2, send=0.4)
        elif pattern == 'epic':
            for off, i in [(0, 1.0), (2, 0.7), (3, 0.5)]:
                mx.add(synth_timpani(i * vel, p), t0 + off, gain=gain, pan=-0.2, send=0.35)


def render_brass_swell(mx, start, num_beats, gain=0.22, vel=0.7):
    pos, idx = 0, 0
    while pos < num_beats - 0.01:
        dur = min(8.0, num_beats - pos)
        notes = CHORD_LIB[CHORD_PROG_12[idx % 12]]
        for k, m in enumerate([notes[1] - 12, notes[0] - 12, notes[1], notes[2] - 12]):
            audio = synth_brass(midi_to_freq(m), dur * BEAT * 0.94, vel=vel,
                                attack=0.1, release=0.15, bright=0.85)
            mx.add(audio, start + pos, gain=gain, pan=(k - 1.5) * 0.15, send=0.5)
        pos += dur;
        idx += 1


def render_tremolo(mx, start, num_beats, gain=0.14, vel=0.9):
    pos, idx = 0, 0
    while pos < num_beats - 0.01:
        notes = CHORD_LIB[CHORD_PROG_12[idx % 12]]
        for k in range(32):
            m = notes[k % 3]
            audio = synth_strings(midi_to_freq(m), BEAT * 0.22, vel=vel * 0.7,
                                  attack=0.005, release=0.02, cutoff=5000)
            mx.add(audio, start + pos + k * 0.25, gain=gain, pan=0, send=0.4)
        pos += 8;
        idx += 1


def render_ostinato(mx, start, num_beats, gain=0.3, vel=0.95):
    pos, idx = 0, 0
    while pos < num_beats - 0.01:
        notes = CHORD_LIB[CHORD_PROG_12[idx % 12]]
        for k in range(16):
            m = notes[k % 3] - 12 if k % 4 != 3 else notes[1]
            audio = synth_strings(midi_to_freq(m), BEAT * 0.4, vel=vel,
                                  attack=0.01, release=0.05, cutoff=4000)
            mx.add(audio, start + pos + k * 0.5, gain=gain, pan=0, send=0.4)
        pos += 8;
        idx += 1


def render_drums_epic(mx, start, num_beats, gain=1.0):
    for bar in range(int(num_beats // 4)):
        t0 = start + bar * 4
        if bar % 4 == 0:
            mx.add(synth_crash(vel=1.0), t0, gain=gain * 0.5, pan=0.4, send=0.5)
            mx.add(synth_bass_drum(vel=1.0), t0, gain=gain * 0.6, pan=0, send=0.15)
        mx.add(synth_bass_drum(vel=0.7), t0 + 2, gain=gain * 0.4, pan=0, send=0.1)


def render_choir_pad(mx, start, num_beats, gain=0.3, vel=1.0):
    pos, idx = 0, 0
    while pos < num_beats - 0.01:
        dur = min(8.0, num_beats - pos)
        notes = CHORD_LIB[CHORD_PROG_12[idx % 12]]
        voices = [notes[0] + 12, notes[1], notes[0], notes[1] - 12]
        for k, m in enumerate(voices):
            audio = synth_choir(midi_to_freq(m), dur * BEAT * 0.95, vel=vel,
                                attack=0.35, release=0.5)
            mx.add(audio, start + pos, gain=gain, pan=(k - 1.5) * 0.2, send=0.7)
        pos += dur;
        idx += 1


# ============================================================ 段落编曲
def sec_intro(mx, start):
    print("  [Intro]  pp  弦乐长音 + 定音鼓远雷 + 竖琴 + 长笛动机")
    render_strings_pad(mx, start, 96, gain=0.35, vel=0.5, attack=0.8)
    for i in range(12):
        mx.add(synth_bass_inst(midi_to_freq(36), 8 * BEAT * 0.95, vel=0.4),
               start + i * 8, gain=0.4, pan=0, send=0.3)
    render_harp(mx, start, 48, gain=0.18, vel=0.6)
    for t in [start + 16, start + 32, start + 48, start + 64, start + 80]:
        mx.add(synth_timpani(vel=0.3, pitch=1.0), t, gain=0.15, pan=-0.3, send=0.6)
    play_note(mx, MAIN[0], start + 32, 'flute', gain=0.15, octave=1, send=0.8, vel=0.6)
    play_note(mx, MAIN[1], start + 34, 'flute', gain=0.12, octave=1, send=0.8, vel=0.6)
    for k in range(16):
        intensity = 0.1 + 0.6 * (k / 16.0)
        mx.add(synth_timpani(vel=intensity, pitch=1.0),
               start + 80 + k * 0.5, gain=0.3, pan=-0.2, send=0.5)


def sec_A1(mx, start):
    print("  [A1]     mp  圆号主旋律 + 弦乐 + 竖琴")
    render_strings_pad(mx, start, 96, gain=0.35, vel=0.7, attack=0.2)
    render_bass(mx, start, 96, gain=0.5, vel=0.7)
    render_harp(mx, start, 96, gain=0.22, vel=0.8)
    render_timpani(mx, start, 96, gain=0.3, pattern='light', vel=0.7)
    play_main(mx, start, 'horn', gain=0.55, send=0.5, vel=0.85)


def sec_B(mx, start):
    """B 段：全程长笛，不切换音色。

    直接调用 play_main 播放完整旋律（含 pickup），
    用长笛的音量做轻微起伏（前半段 0.42，后半段 0.45）避免单调。
    """
    print("  [B]      mp  长笛主旋律（全程长笛）")
    render_strings_pad(mx, start, 96, gain=0.30, vel=0.60, attack=0.25)
    render_bass(mx, start, 96, gain=0.45, vel=0.65)
    render_timpani(mx, start, 96, gain=0.25, pattern='light', vel=0.65)
    play_main(mx, start, 'flute', gain=0.42, send=0.50, vel=0.85)


def sec_A2(mx, start):
    print("  [A2]     mf  弦乐全奏主旋律 + 圆号助奏")
    render_strings_pad(mx, start, 96, gain=0.45, vel=0.85, attack=0.1)
    render_bass(mx, start, 96, gain=0.6, vel=0.85)
    render_harp(mx, start, 96, gain=0.25, vel=0.9)
    render_timpani(mx, start, 96, gain=0.4, pattern='heavy', vel=0.85)
    render_brass_swell(mx, start, 96, gain=0.22, vel=0.7)
    play_main(mx, start, 'strings', gain=0.55, send=0.5, vel=0.9)
    play_main(mx, start, 'horn', gain=0.25, send=0.55, vel=0.8, with_pickup=False)


def sec_C1(mx, start):
    print("  [C1]     f   铜管齐奏 + 弦乐 tremolo + 定音鼓 epic")
    render_strings_pad(mx, start, 96, gain=0.4, vel=0.95, attack=0.08)
    play_main(mx, start, 'trumpet', gain=0.55, send=0.5, vel=1.0)
    play_main(mx, start, 'horn', gain=0.3, send=0.5, vel=0.9, with_pickup=False)
    play_main(mx, start, 'trombone', gain=0.25, send=0.5, vel=0.9, with_pickup=False)
    render_bass(mx, start, 96, gain=0.6, vel=1.0)
    render_tremolo(mx, start, 96, gain=0.14, vel=0.9)
    render_timpani(mx, start, 96, gain=0.55, pattern='epic', vel=1.0)
    render_drums_epic(mx, start, 96, gain=0.8)
    render_harp(mx, start, 96, gain=0.2, vel=0.9)


def sec_C2(mx, start):
    print("  [C2]     ff  全奏 · 最高潮 · 合唱")
    render_strings_pad(mx, start, 96, gain=0.45, vel=1.0, attack=0.06)
    play_main(mx, start, 'trumpet', gain=0.6, send=0.5, vel=1.0)
    play_main(mx, start, 'horn', gain=0.35, send=0.5, vel=1.0, with_pickup=False)
    play_main(mx, start, 'trombone', gain=0.3, send=0.5, vel=1.0, with_pickup=False)
    play_main(mx, start, 'flute', gain=0.2, octave=1, send=0.6, vel=0.95, with_pickup=False)
    render_choir_pad(mx, start, 96, gain=0.3, vel=1.0)
    render_bass(mx, start, 96, gain=0.65, vel=1.0)
    render_ostinato(mx, start, 96, gain=0.3, vel=0.95)
    render_timpani(mx, start, 96, gain=0.65, pattern='roll', vel=1.0)
    render_drums_epic(mx, start, 96, gain=1.0)
    render_harp(mx, start, 96, gain=0.15, vel=0.85)


def sec_outro1(mx, start):
    print("  [Outro1] mf  圆号主旋律 · 退潮")
    render_strings_pad(mx, start, 96, gain=0.35, vel=0.65, attack=0.3)
    render_bass(mx, start, 96, gain=0.45, vel=0.65)
    render_harp(mx, start, 96, gain=0.2, vel=0.7)
    render_timpani(mx, start, 96, gain=0.3, pattern='light', vel=0.6)
    play_main(mx, start, 'horn', gain=0.5, send=0.55, vel=0.85)
    play_main(mx, start, 'strings', gain=0.2, send=0.6, vel=0.7, with_pickup=False)


def sec_outro2(mx, start):
    print("  [Outro2] p   尾声 · 独奏回响 + Picardy third")
    render_strings_pad(mx, start, 96, gain=0.25, vel=0.5, attack=0.5)
    render_harp(mx, start, 48, gain=0.15, vel=0.5)

    if start > 0:
        _play_melody_events(mx, PICKUP, start - PICKUP_LEN, 'violin',
                            gain=0.28, send=0.7, vel=0.7)

    _play_melody_events(mx, MAIN[:5], start, 'violin',
                        gain=0.32, send=0.7, vel=0.75)
    _play_melody_events(mx, MAIN[:5], start + 32, 'flute',
                        gain=0.15, octave=1, send=0.8, vel=0.6)

    for t in [start + 16, start + 48, start + 76]:
        mx.add(synth_timpani(vel=0.25, pitch=1.0), t, gain=0.15, pan=-0.3, send=0.7)

    end = start + 88
    for m, pan in [(48, -0.4), (60, -0.2), (64, 0), (67, 0.2), (72, 0.4)]:
        audio = synth_strings(midi_to_freq(m), 8 * BEAT, vel=0.45,
                              attack=0.5, release=1.5)
        mx.add(audio, end, gain=0.25, pan=pan, send=0.85)


# ============================================================ 混响 / 母带
def make_ir(dur=4.0, seed=42):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    ir = np.zeros((2, n), dtype=np.float32)
    for ch in range(2):
        x = rng.standard_normal(n).astype(np.float32)
        ir[ch] = (_lowpass(x, 400) * np.exp(-t / 1.5)
                  + _bandpass(x, 400, 4000) * np.exp(-t / 1.0) * 0.7
                  + _highpass(x, 4000) * np.exp(-t / 0.5) * 0.35)
        ir[ch] *= np.minimum(1, t / 0.01)
        ir[ch] /= np.sqrt(np.sum(ir[ch] ** 2)) + 1e-9
    return ir


def apply_reverb(mx, wet_gain=0.55):
    ir = make_ir(4.0)
    wet = np.zeros_like(mx.send)
    for ch in range(2):
        wet[ch] = fftconvolve(mx.send[ch], ir[ch])[:N].astype(np.float32)
    return mx.buf + wet * wet_gain


def master(mix):
    for ch in range(2):
        mix[ch] = _highpass(mix[ch], 30)
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.85
    L = int(0.005 * SR)
    pk = maximum_filter1d(np.max(np.abs(mix), axis=0), size=2 * L + 1)
    g = np.minimum(1.0, 0.82 / (pk + 1e-9))
    a = np.exp(-1.0 / (0.1 * SR))
    gs = lfilter([1 - a], [1, -a], g)
    mix = mix * np.minimum(g, gs)
    mix = np.tanh(mix * 1.08) / 1.08
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.85
    fade_in, fade_out = int(0.8 * SR), int(4.0 * SR)
    mix[:, :fade_in] *= np.linspace(0, 1, fade_in)
    mix[:, -fade_out:] *= np.linspace(1, 0, fade_out)
    return mix


# ============================================================ MIDI
def vlq(n):
    out = [n & 0x7F];
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80);
        n >>= 7
    return bytes(reversed(out))


TPQ = 480


def _melody_to_events(melody, t_start, octave_off, vel, channel=0):
    evs = [];
    t = t_start
    for ev in melody:
        m = NAME_TO_MIDI[ev[0]] + octave_off * 12
        s = int(round(t * TPQ));
        e = int(round((t + ev[1] * 0.95) * TPQ))
        evs.append((s, 1, bytes([0x90 | channel, m, vel])))
        evs.append((e, 0, bytes([0x80 | channel, m, 64])))
        t += ev[1]
    return evs


def build_midi(path, bpm=BPM):
    tempo_us = int(60_000_000 / bpm)
    trk = bytearray()
    trk += vlq(0) + bytes([0xFF, 0x51, 0x03]) + tempo_us.to_bytes(3, 'big')

    for ch, prog in [(0, 0), (1, 60), (2, 48), (3, 47)]:
        trk += vlq(0) + bytes([0xC0 | ch, prog])

    evs = []
    for sec_start, oct_off, vel in [(96, 0, 80), (192, 1, 70), (288, 0, 88),
                                    (384, 0, 95), (480, 0, 100), (576, 0, 78)]:
        evs += _melody_to_events(PICKUP, sec_start - PICKUP_LEN, oct_off, vel - 8, ch=0)
        evs += _melody_to_events(MAIN, sec_start, oct_off, vel, ch=0)

    for sec_start in [384, 480]:
        evs += _melody_to_events(MAIN, sec_start, 0, 92, ch=1)

    for sec_start in [96, 192, 288, 384, 480, 576]:
        for bar in range(24):
            bass = CHORD_BASS_MIDI[CHORD_PROG_12[(bar // 2) % 12]]
            t = sec_start + bar * 4
            s = int(round(t * TPQ));
            e = int(round((t + 3.8) * TPQ))
            evs.append((s, 1, bytes([0x90 | 2, bass, 85])))
            evs.append((e, 0, bytes([0x80 | 2, bass, 64])))

    for sec_start in [96, 288, 384, 480]:
        for bar in range(24):
            t = sec_start + bar * 4
            s = int(round(t * TPQ));
            e = int(round((t + 0.5) * TPQ))
            evs.append((s, 1, bytes([0x90 | 3, 43, 100])))
            evs.append((e, 0, bytes([0x80 | 3, 43, 64])))

    evs.sort(key=lambda x: (x[0], x[1]))
    prev = 0
    for tick, _, data in evs:
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
    mix = apply_reverb(mx, wet_gain=0.55)
    print("母带 ...")
    mix = master(mix)

    pcm = (mix.T * 32700).astype(np.int16)
    sf.write('piano_epic_4min.wav', pcm, SR, subtype='PCM_16')
    print(f"✅ piano_epic_4min.wav  {len(mix[0]) / SR:.2f}s")

    build_midi('piano_epic_4min.mid')
    print("✅ piano_epic_4min.mid")


if __name__ == '__main__':
    main()
