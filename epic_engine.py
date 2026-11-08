# -*- coding: utf-8 -*-
"""epic_engine —— 好莱坞史诗交响配乐渲染引擎

架构：
  SSO 采样层 (pysfizz)  →  分轨 bus  →  分轨处理(EQ/压缩/侧链/混响)  →  premaster
  原脚本合成层 (harp/bass/choir/kick) 作为 hybrid 层叠加
  →  母带链(EQ→胶水压缩→饱和→限幅→响度对齐)  →  epic_final.wav + MIDI + 报告

所有音乐参数（乐器选择、力度、织体、打击乐密度、混音、母带）都由 profile 字典控制，
v1..v5 系列脚本只改 profile，不改引擎。
"""
import os, sys, json, math, time
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve, lfilter, resample_poly
from scipy.ndimage import maximum_filter1d

try:
    from pysfizz import Synth
except Exception:  # pragma: no cover
    Synth = None

# ============================================================ 基础参数
SR = 48000
BPM = 192
BEAT = 60.0 / BPM  # 0.3125 s
DUR = 240.0
N = int(SR * DUR)
TOTAL_BEATS = 768
SEC_LEN = 96  # 每段 96 拍 = 30 s
assert TOTAL_BEATS // SEC_LEN == 8

HERE = os.path.dirname(os.path.abspath(__file__))
# pysfizz/sfizz 只能处理 ASCII 路径；用 ASCII junction（D:\_sso）指向采样库
_ASCII_LINK = 'D:/_sso'
SSO_ROOT = _ASCII_LINK if os.path.isdir(_ASCII_LINK) else os.path.join(
    HERE, 'soundfonts', 'Sonatina Symphonic Orchestra')

# ============================================================ 音高 & 旋律（与原脚本一致）
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
PICKUP_LEN = sum(e[1] for e in PICKUP)  # 2
MAIN_LEN = sum(e[1] for e in MAIN)  # 77


def midi_to_freq(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ============================================================ 和声（C 和声小调 + 那不勒斯 + 皮卡迪三度）
CHORDS = {
    'Cm': ([60, 63, 67], 36),
    'Ab': ([56, 60, 63], 32),
    'Fm': ([53, 56, 60], 29),
    'G': ([55, 59, 62], 31),
    'Db': ([62, 65, 69], 38),  # 那不勒斯 ♭II 大三和弦
    'C': ([60, 64, 67], 36),  # 皮卡迪三度终止
}
CHORD_PROG_12 = ['Cm', 'Ab', 'Fm', 'G'] * 3


def chord_at(sec, bar):
    """返回第 sec 段第 bar 小节的调式和弦。C1 尾部升 Db，C2 尾部收 Cm，Outro2 收 C。"""
    if sec == 4 and bar >= 20:
        return 'Db'
    if sec == 5:
        if bar >= 20:
            return 'Cm'
        if bar == 19:
            return 'G'
    if sec == 7:
        if bar >= 20:
            return 'C'
        if bar >= 18:
            return 'G'
    return CHORD_PROG_12[(bar // 2) % 12]


def voicing(kind, name):
    """按音色角色给出具体 MIDI 声部（含低八度叠置）。"""
    n = CHORDS[name][0]
    if kind == 'string_pad':
        return [n[0] - 12, n[1] - 12, n[0], n[1], n[2], n[2] + 12]
    if kind == 'string_low':
        return [n[0] - 12, n[1] - 12]
    if kind == 'root_bass':
        return [n[0] - 24, n[0] - 12]
    if kind == 'brass_harmony':
        return [n[0] - 12, n[1] - 12, n[2] - 12, n[0]]
    if kind == 'choir':
        return [n[0] - 12, n[1] - 12, n[2] - 12, n[0], n[1]]
    if kind == 'tutti':
        return [n[0] - 24, n[0] - 12, n[1] - 12, n[2] - 12, n[0], n[1], n[2], n[2] + 12]
    return [n[0], n[1], n[2]]


# ============================================================ 采样乐器注册表
INST = {
    # 铜管
    'horn': 'Brass - Notation/Horn Solo Sustain (looped).sfz',
    'horn_marc': 'Brass - Notation/Horn Solo Marcato (looped).sfz',
    'horns': 'Brass - Notation/Horns Sustain.sfz',
    'horns_marc': 'Brass - Notation/Horns Marcato.sfz',
    'trumpet': 'Brass - Notation/Trumpet Solo Sustain (looped).sfz',
    'trumpet_marc': 'Brass - Notation/Trumpet Solo Marcato (looped).sfz',
    'trumpets': 'Brass - Notation/Trumpets Sustain.sfz',
    'trumpets_marc': 'Brass - Notation/Trumpets Marcato.sfz',
    'trombones': 'Brass - Notation/Trombones Sustain.sfz',
    'trombones_marc': 'Brass - Notation/Trombones Marcato.sfz',
    'trombones_stac': 'Brass - Notation/Trombones Staccato.sfz',
    'bass_trombone': 'Brass - Notation/Bass Trombone Solo Sustain (looped).sfz',
    'tuba': 'Brass - Notation/Tuba Sustain.sfz',
    'tuba_stac': 'Brass - Notation/Tuba Staccato.sfz',
    'brass_all': 'Brass - Notation/All Brass Sustain.sfz',
    'brass_all_marc': 'Brass - Notation/All Brass Marcato.sfz',
    # 弦乐
    'strings_all': 'Strings - Notation/All Strings Sustain.sfz',
    'tremolo': 'Strings - Notation/All Strings Tremolo.sfz',
    'celli': 'Strings - Notation/Celli Sustain.sfz',
    'celli_marc': 'Strings - Notation/Celli Marcato.sfz',
    'basses': 'Strings - Notation/Basses Sustain.sfz',
    'basses_marc': 'Strings - Notation/Basses Marcato.sfz',
    'violin_solo': 'Strings - Notation/Violin Solo 1 Sustain (looped).sfz',
    # 木管
    'flute': 'Woodwinds - Notation/Flute Solo 1 Sustain (looped).sfz',
    'oboe': 'Woodwinds - Notation/Oboe Solo Sustain (looped).sfz',
    'piccolo': 'Woodwinds - Notation/Piccolo Solo Sustain (looped).sfz',
    # 打击乐
    'timpani': 'Percussion/Timpani.sfz',
    'drumkit': 'Percussion/Bass Drum & Snare.sfz',
    'cymbals': 'Percussion/Cymbals & Tamtam.sfz',
    'glock': 'Percussion/Glockenspiel.sfz',
    'triangle': 'Percussion/Triangle.sfz',
    # 合唱
    'choir': 'Chorus - Notation/Mixed Chorus.sfz',
    'chorus_big': 'Chorus - Notation/Large Chrous.sfz',
}

# 乐器响度微调（线性增益），平衡不同 patch 的原始电平
INST_TRIM = {
    'horn': 1.0, 'horn_marc': 1.0, 'horns': 0.95, 'horns_marc': 0.95,
    'trumpet': 0.9, 'trumpet_marc': 0.9, 'trumpets': 0.85, 'trumpets_marc': 0.85,
    'trombones': 0.9, 'trombones_marc': 0.9, 'trombones_stac': 0.9,
    'bass_trombone': 0.95, 'tuba': 0.9, 'tuba_stac': 0.9,
    'brass_all': 0.75, 'brass_all_marc': 0.75, 'brass_all_stac': 0.75,
    'strings_all': 0.8, 'tremolo': 0.85, 'strings_marc': 0.85, 'strings_stac': 0.85,
    'celli': 0.95, 'celli_marc': 0.95, 'basses': 1.0, 'basses_marc': 1.0,
    'violas': 0.9, 'violas_trem': 0.85, 'violins': 0.9, 'violins_trem': 0.85,
    'violins_marc': 0.85, 'violin_solo': 1.0, 'violin_solo_marc': 1.0,
    'winds_all': 0.8, 'flute': 0.9, 'flute_marc': 0.9, 'oboe': 0.9,
    'oboe_marc': 0.9, 'bassoon': 0.95, 'bassoons': 0.9, 'piccolo': 0.85,
    'choir': 0.85, 'chorus_big': 0.7,
}

# 打击乐 MIDI 键位（依据 SSO Percussion/*.sfz 的实际 region 映射）
# Timpani 击打区 36..48（C2..C3，region 内可微分调音）；滚奏 60..72；渐强滚奏 84..96
PERC = {
    'bass_drum': 48,  # Bass Drum & Snare: key=c3
    'snare': 49,  # key=c#3
    'snare_roll': 50,  # key=d3
    'crash': 52,  # Cymbals & Tamtam: g3 = piatti
    'cymb_roll_f': 48,  # c3 = cymbal_roll f
    'cymb_roll_mf': 49,  # d3
    'cymb_roll_p': 50,  # e3
    'tamtam': 57,  # a3
    'glock_c': 72,
}


# ============================================================ 采样器
class Sampler:
    def __init__(self, root=SSO_ROOT, cache_path=None, sr=SR):
        self.root = root
        self.sr = sr
        self.synths = {}
        self.cache = {}
        self.cache_path = cache_path
        self.hits = 0
        self.misses = 0
        if cache_path and os.path.exists(cache_path):
            try:
                z = np.load(cache_path, allow_pickle=False)
                for k in z.files:
                    self.cache[k] = z[k]
                print(f'  [sampler] 载入磁盘缓存 {len(self.cache)} 条', flush=True)
            except Exception as e:
                print('  [sampler] 缓存载入失败', e, flush=True)

    def synth(self, inst):
        if inst not in self.synths:
            path = os.path.join(self.root, INST[inst])
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            s = Synth(sample_rate=self.sr, block_size=256)
            ok = s.load_sfz_file(path)
            if not ok:
                raise RuntimeError(f'load failed {path}')
            self.synths[inst] = s
        return self.synths[inst]

    def note(self, inst, pitch, vel, on_dur, tail=0.35):
        """渲染单音（带缓存）。pitch 会自动 clamp 到 0..127。"""
        pitch = int(max(0, min(127, pitch)))
        vel = int(max(1, min(127, vel)))
        on_q = max(1, int(round(on_dur * 100)))
        t_q = int(round(tail * 100))
        key = f'{inst}|{pitch}|{vel}|{on_q}|{t_q}'
        a = self.cache.get(key)
        if a is None:
            self.misses += 1
            s = self.synth(inst)
            render_dur = on_q / 100.0 + t_q / 100.0
            a = s.render_note(pitch, vel, on_q / 100.0, render_dur)
            a = np.ascontiguousarray(np.asarray(a, dtype=np.float32))
            a *= INST_TRIM.get(inst, 1.0)
            self.cache[key] = a
        else:
            self.hits += 1
        return a

    def save_cache(self):
        if not self.cache_path:
            return
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        np.savez(self.cache_path, **self.cache)
        print(f'  [sampler] 写入缓存 {len(self.cache)} 条 → {self.cache_path}', flush=True)


# ============================================================ 原脚本合成层（保留作 hybrid 层）
def _lowpass(x, cutoff, order=2):
    cutoff = min(max(cutoff, 20), SR * 0.45)
    return sosfilt(butter(order, cutoff, 'low', fs=SR, output='sos'), x).astype(np.float32)


def _highpass(x, cutoff, order=2):
    cutoff = min(max(cutoff, 20), SR * 0.45)
    return sosfilt(butter(order, cutoff, 'high', fs=SR, output='sos'), x).astype(np.float32)


def _bandpass(x, lo, hi, order=2):
    lo = max(lo, 20)
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


def synth_bass_inst(freq, dur_s, vel=1.0):
    n = int((dur_s + 0.15) * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    audio = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t)
             + 0.1 * np.sin(6 * np.pi * freq * t))
    bow = _bandpass(np.random.randn(n).astype(np.float32), 100, 800) * 0.08
    audio = (audio + bow).astype(np.float32)
    return (audio * _env(n, 0.06, 0.15) * vel * 0.22).astype(np.float32)


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


def synth_bass_drum(vel=1.0):
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    f = 38 + 30 * np.exp(-t / 0.1)
    phase = 2 * np.pi * np.cumsum(f) / SR
    audio = np.sin(phase) * np.exp(-t / 0.5)
    click = np.random.randn(n).astype(np.float32) * np.exp(-t / 0.005) * 0.3
    return (np.tanh(audio + click) * vel * 0.55).astype(np.float32)


# ============================================================ 混音器
BUSES = ['lead', 'brass', 'low', 'strings', 'perc', 'choir']


class Mixer:
    def __init__(self):
        self.buf = {b: np.zeros((2, N), dtype=np.float32) for b in BUSES}
        self.send = {'long': np.zeros((2, N), dtype=np.float32),
                     'short': np.zeros((2, N), dtype=np.float32)}
        self.kick = np.zeros(N, dtype=np.float32)
        self.events = []  # (beat, channel, midi, dur_beats, vel) 用于导出 MIDI

    def add(self, bus, audio, beat_pos, gain=1.0, pan=0.0, send=0.5,
            send_kind='long', midi=None, kick=False):
        if audio.ndim == 1:
            audio = audio[np.newaxis, :]
        if audio.shape[0] == 1:
            audio = np.repeat(audio, 2, axis=0)
        i = int(round(beat_pos * BEAT * SR))
        if i >= N:
            return
        if i < 0:
            audio = audio[:, -i:]
            i = 0
        n = min(audio.shape[1], N - i)
        if n <= 0:
            return
        a = (pan + 1) * np.pi / 4
        lg, rg = float(np.cos(a)) * 1.41421356, float(np.sin(a)) * 1.41421356
        seg = audio[:, :n] * gain
        self.buf[bus][0, i:i + n] += seg[0] * lg
        self.buf[bus][1, i:i + n] += seg[1] * rg
        if send:
            s = self.send[send_kind]
            s[0, i:i + n] += seg[0] * lg * send
            s[1, i:i + n] += seg[1] * rg * send
        if kick:
            self.kick[i:i + n] += np.abs(seg[0]) + np.abs(seg[1])
        if midi is not None:
            ch, pitch, dur_beats, vel = midi
            self.events.append((beat_pos, ch, int(pitch), float(dur_beats), int(vel)))


# ============================================================ 编曲辅助
class Orchestrator:
    def __init__(self, profile):
        self.p = profile
        self.samp = Sampler(cache_path=os.path.join(HERE, 'cache', profile.get('cache_name', 'notes.npz')))
        self.mx = Mixer()

    # ---------------------------------------------------------- 基础积木
    def note(self, bus, inst, pitch, beat_pos, dur_beats, vel, gain, pan=0.0,
             send=0.5, send_kind='long', ch=None, marc=False):
        on_dur = max(0.06, dur_beats * BEAT * 0.97)
        tail = 0.28 if bus != 'perc' else 0.9
        audio = self.samp.note(inst, pitch, vel, on_dur, tail)
        midi = (ch, pitch, dur_beats, vel) if ch is not None else None
        self.mx.add(bus, audio, beat_pos, gain=gain, pan=pan, send=send,
                    send_kind=send_kind, midi=midi)

    def melody(self, inst, start_beat, gain, vel, octave=0, bus='lead', ch=0,
               with_pickup=True, marc_first=True):
        pos = 0.0
        if with_pickup and start_beat > 0:
            for ev in PICKUP:
                p = NAME_TO_MIDI[ev[0]] + 12 * octave
                self.note(bus, inst, p, start_beat - PICKUP_LEN + pos, ev[1],
                          int(vel * 0.85), gain * 0.9, send=0.55, ch=ch)
                pos += ev[1]
        pos = 0.0
        for ev in MAIN:
            p = NAME_TO_MIDI[ev[0]] + 12 * octave
            self.note(bus, inst, p, start_beat + pos, ev[1], vel, gain,
                      send=0.55, ch=ch)
            pos += ev[1]

    def melody_short(self, melody, start_beat, inst, gain, vel, octave=0,
                     bus='lead', ch=0, prec_pickup=False):
        if prec_pickup and start_beat > 0:
            pos = -PICKUP_LEN
            for ev in PICKUP:
                self.note(bus, inst, NAME_TO_MIDI[ev[0]] + 12 * octave,
                          start_beat + pos, ev[1], int(vel * 0.85), gain * 0.9,
                          send=0.6, ch=ch)
                pos += ev[1]
        pos = 0.0
        for ev in melody:
            self.note(bus, inst, NAME_TO_MIDI[ev[0]] + 12 * octave,
                      start_beat + pos, ev[1], vel, gain, send=0.6, ch=ch)
            pos += ev[1]

    # ---------------------------------------------------------- 和声织体
    def chord_pad(self, bus, inst, sec, bar0, bar1, kind, vel, gain,
                  pan_spread=0.35, send=0.55, dur_scale=0.97, ch=None):
        for bar in range(bar0, bar1, 2):
            name = chord_at(sec, bar)
            notes = voicing(kind, name)
            beat0 = sec * SEC_LEN + bar * 4
            for k, p in enumerate(notes):
                pan = pan_spread * (k / max(1, len(notes) - 1) - 0.5) * 2
                self.note(bus, inst, p, beat0, 8 * dur_scale, vel, gain,
                          pan=pan, send=send, ch=ch)

    def low_brass_ostinato(self, sec, bar0, bar1, vel, gain, pattern='eighths',
                           ch=1, bus='low'):
        """长号+大号 固定音型：根音八分音符，第 4 个八分换五度。"""
        for bar in range(bar0, bar1):
            name = chord_at(sec, bar)
            root = CHORDS[name][1]
            third = CHORDS[name][0][2]
            beat0 = sec * SEC_LEN + bar * 4
            if pattern == 'eighths':
                for k in range(8):
                    p = root if k != 3 else third - 12
                    mk = 'trombones' if k % 2 == 0 else 'trombones_marc'
                    self.note(bus, mk, p + 12, beat0 + k * 0.5, 0.46, vel,
                              gain, send=0.3, ch=ch, marc=True)
                # 大号在 1、3 拍补重量
                self.note(bus, 'tuba', root, beat0, 1.2, vel, gain * 0.8, send=0.25, ch=ch)
                self.note(bus, 'tuba', root, beat0 + 2, 1.2, vel, gain * 0.8, send=0.25, ch=ch)
            elif pattern == 'triplet':
                for k in range(12):
                    p = root if k % 4 != 3 else third - 12
                    self.note(bus, 'trombones', p + 12, beat0 + k / 3.0, 0.28,
                              vel, gain * 0.9, send=0.3, ch=ch)

    def string_ostinato(self, sec, bar0, bar1, vel, gain, ch=3, bus='strings'):
        for bar in range(bar0, bar1):
            name = chord_at(sec, bar)
            n = CHORDS[name][0]
            beat0 = sec * SEC_LEN + bar * 4
            for k in range(8):
                p = [n[0] - 12, n[1] - 12, n[2] - 12, n[1] - 12][k % 4]
                inst = 'celli_marc' if k % 2 == 0 else 'basses_marc'
                self.note(bus, inst, p, beat0 + k * 0.5, 0.46, vel, gain,
                          send=0.4, ch=ch, marc=True)

    def tremolo_pad(self, bus, sec, bar0, bar1, notes_off, vel, gain, inst='tremolo',
                    send=0.5, ch=3):
        for bar in range(bar0, bar1, 2):
            name = chord_at(sec, bar)
            n = CHORDS[name][0]
            beat0 = sec * SEC_LEN + bar * 4
            for k, off in enumerate(notes_off):
                p = n[k % 3] + off
                self.note(bus, inst, p, beat0, 7.7, vel, gain,
                          pan=0.25 * (k / max(1, len(notes_off) - 1) - 0.5) * 2,
                          send=send, ch=ch)

    def brass_stab(self, sec, bar, vel, gain, kind='tutti', dur=0.4, bus='brass',
                   send=0.5, ch=0, inst=None):
        name = chord_at(sec, bar)
        beat0 = sec * SEC_LEN + bar * 4
        notes = voicing(kind, name)
        for k, p in enumerate(notes):
            ii = inst or ('brass_all_marc' if dur < 1.0 else 'brass_all')
            self.note(bus, ii, p, beat0, dur, vel, gain,
                      pan=0.3 * (k / max(1, len(notes) - 1) - 0.5) * 2,
                      send=send, ch=ch)

    # ---------------------------------------------------------- 打击乐（结构声部）
    def timpani(self, beat_pos, vel, gain, note=None, send=0.45):
        p = note if note is not None else 36
        audio = self.samp.note('timpani', p, int(vel), 0.14, 1.3)
        self.mx.add('perc', audio, beat_pos, gain=gain, pan=-0.25, send=send,
                    send_kind='short', midi=(2, p, 0.5, int(vel)))

    def bass_drum(self, beat_pos, vel, gain, send=0.35, kick=True, ch=2):
        audio = self.samp.note('drumkit', PERC['bass_drum'], int(vel), 0.12, 1.0)
        self.mx.add('perc', audio, beat_pos, gain=gain, pan=0.0, send=send,
                    send_kind='short', midi=(ch, PERC['bass_drum'], 0.5, int(vel)),
                    kick=kick)

    def snare(self, beat_pos, vel, gain, send=0.3, ch=2):
        audio = self.samp.note('drumkit', PERC['snare'], int(vel), 0.08, 0.6)
        self.mx.add('perc', audio, beat_pos, gain=gain, pan=0.15, send=send,
                    send_kind='short', midi=(ch, PERC['snare'], 0.25, int(vel)))

    def crash(self, beat_pos, vel, gain, send=0.3, ch=2):
        audio = self.samp.note('cymbals', PERC['crash'], int(vel), 0.3, 2.2)
        self.mx.add('perc', audio, beat_pos, gain=gain, pan=0.4, send=send,
                    send_kind='short', midi=(ch, PERC['crash'], 2.0, int(vel)))

    def glock(self, beat_pos, pitch, vel, gain, send=0.4, ch=2):
        audio = self.samp.note('glock', pitch, int(vel), 0.1, 1.2)
        self.mx.add('perc', audio, beat_pos, gain=gain, pan=0.35, send=send,
                    send_kind='short', midi=(ch, pitch, 1.0, int(vel)))

    def timp_roll(self, beat_pos, beats, vel0, vel1, gain, step=0.25, send=0.45):
        k = 0
        t = 0.0
        while t < beats:
            r = t / max(beats, 1e-9)
            v = int(vel0 + (vel1 - vel0) * r)
            self.timpani(beat_pos + t, v, gain * (0.7 + 0.3 * r), send=send)
            t += step
            k += 1

    # ---------------------------------------------------------- hybrid 层
    def sub_bass(self, beat_pos, dur_beats, freq, vel, gain, send=0.15):
        a = synth_bass_inst(freq, dur_beats * BEAT * 0.95, vel=vel)
        self.mx.add('low', a[np.newaxis, :], beat_pos, gain=gain, pan=0, send=send)

    def harp_arp(self, sec, bar0, bar1, vel, gain):
        for bar in range(bar0, bar1, 2):
            name = chord_at(sec, bar)
            n = CHORDS[name][0]
            arp = [n[0] - 12, n[1] - 12, n[2] - 12, n[0], n[1], n[2], n[0] + 12, n[1] + 12]
            beat0 = sec * SEC_LEN + bar * 4
            for k, p in enumerate(arp):
                a = synth_harp(midi_to_freq(p), 0.5, vel=vel * 0.7)
                self.mx.add('strings', a[np.newaxis, :], beat0 + k * 0.5,
                            gain=gain, pan=0.3, send=0.6)

    def choir_synth_pad(self, sec, bar0, bar1, vel, gain, ch=4):
        """原脚本 synth_choir 作为 hybrid 层，与 SSO 合唱叠加。"""
        for bar in range(bar0, bar1, 2):
            name = chord_at(sec, bar)
            for k, p in enumerate(voicing('choir', name)):
                a = synth_choir(midi_to_freq(p), 8 * BEAT * 0.95, vel=vel,
                                attack=0.35, release=0.5)
                self.mx.add('choir', a[np.newaxis, :], sec * SEC_LEN + bar * 4,
                            gain=gain, pan=0.2 * (k - 2), send=0.7)

    # ---------------------------------------------------------- 段落
    def sec_intro(self, S):
        p, d = self.p, self.p.get('density', 1.0)
        pg = self.p.get('perc_gain', 1.0)
        ig = self.p.get('intro_gain', 1.0)
        # 低音弦乐 tremolo（远处雷声般的压迫）
        self.tremolo_pad('strings', 0, 0, 24, [-12], vel=int(40 * ig), gain=0.42 * ig)
        self.chord_pad('strings', 'celli', 0, 0, 24, 'string_low', vel=int(34 * ig),
                       gain=0.30 * ig)
        # sub 低音（hybrid 层）
        for k in range(12):
            self.sub_bass(S + k * 8, 8, midi_to_freq(36), 0.35, 0.28 * ig)
        # 心跳大鼓：每 2 拍一次
        for bar in range(3, 20):
            self.bass_drum(S + bar * 4 + 1.5, 45, 0.14 * pg, kick=False)
        # 远处定音鼓
        for bar in (4, 9, 14, 19):
            self.timpani(S + bar * 4, 45, 0.16 * pg)
        # 竖琴
        self.harp_arp(0, 0, 16, vel=0.45, gain=0.10 * ig)
        # 长笛动机（主题预告）
        self.note('lead', 'flute', NAME_TO_MIDI['+1'], S + 32, 6, 55, 0.10 * ig,
                  send=0.75, ch=0)
        self.note('lead', 'flute', NAME_TO_MIDI['#6'], S + 38, 1, 45, 0.07 * ig,
                  send=0.75, ch=0)
        # 滚奏 riser 进入 A1
        self.timp_roll(S + 80, 16, 30, 95, 0.20 * pg)

    def sec_A1(self, S):
        p = self.p
        lg = p.get('lead_gain', 1.0)
        # 弦乐：温暖层
        self.chord_pad('strings', 'strings_all', 1, 0, 24, 'string_pad', vel=62, gain=0.32)
        self.chord_pad('strings', 'celli', 1, 0, 24, 'string_low', vel=55, gain=0.36)
        # 低音铜管长音铺底
        self.chord_pad('low', 'trombones', 1, 0, 24, 'string_low', vel=48, gain=0.30)
        self.chord_pad('low', 'tuba', 1, 0, 24, 'root_bass', vel=45, gain=0.24)
        # ★ 圆号独奏主旋律
        self.melody('horn', S, 0.52 * lg, 80, bus='lead', ch=0)
        self.harp_arp(1, 0, 24, vel=0.7, gain=0.10)
        # 定音鼓心跳 + 小军鼓弱击（行军感）
        for bar in range(24):
            self.timpani(S + bar * 4, 62, 0.22, note=self.timp_note(1, bar))
            if bar % 2 == 0:
                self.snare(S + bar * 4 + 2, 42, 0.07)

    def sec_B(self, S):
        p = self.p
        lg = p.get('lead_gain', 1.0)
        self.chord_pad('strings', 'strings_all', 2, 0, 24, 'string_pad', vel=52, gain=0.26)
        self.chord_pad('strings', 'celli', 2, 0, 24, 'string_low', vel=48, gain=0.30)
        # 铜管退到和声长音
        self.chord_pad('brass', 'horns', 2, 0, 24, 'brass_harmony', vel=45, gain=0.20)
        self.chord_pad('low', 'tuba', 2, 0, 24, 'root_bass', vel=38, gain=0.16)
        # ★ 长笛主旋律（双簧管弱叠）
        self.melody('flute', S, 0.40 * lg, 72, bus='lead', ch=0)
        self.melody('oboe', S, 0.10 * lg, 58, bus='lead', with_pickup=False)
        self.harp_arp(2, 0, 24, vel=0.6, gain=0.09)
        for bar in range(24):
            self.timpani(S + bar * 4, 48, 0.14, note=self.timp_note(2, bar))

    def sec_A2(self, S):
        p = self.p
        lg = p.get('lead_gain', 1.0)
        d = p.get('density', 1.0)
        self.chord_pad('strings', 'strings_all', 3, 0, 24, 'string_pad', vel=75, gain=0.36)
        self.string_ostinato(3, 0, 24, vel=82, gain=0.26)
        self.chord_pad('brass', 'horns', 3, 0, 24, 'brass_harmony', vel=62, gain=0.18)
        # ★ 小号接过主旋律 + 圆号助奏
        self.melody('trumpet', S, 0.58 * lg, 92, bus='lead', ch=0)
        self.melody('horns', S, 0.20, 78, octave=-1, bus='brass', with_pickup=False)
        # 低音铜管八分音符推进
        self.low_brass_ostinato(3, 0, 24, vel=86, gain=0.42)
        self.harp_arp(3, 0, 24, vel=0.7, gain=0.09)
        for bar in range(24):
            self.timpani(S + bar * 4, 86, 0.28, note=self.timp_note(3, bar))
            self.timpani(S + bar * 4 + 2, 60, 0.18, note=self.timp_note(3, bar))
        # 后半段小军鼓加密
        for bar in range(12, 24):
            for k in range(8):
                if (k + bar) % 2 == 0 or d > 1.0:
                    self.snare(S + bar * 4 + k * 0.5, 55, 0.08)
        # 圆号对位（v3 起启用）：与主旋律反向的三度/五度摆动
        if p.get('a2_counter', False):
            for bar in range(0, 20):
                name = chord_at(3, bar)
                n = CHORDS[name][0]
                b0 = S + bar * 4
                for k in range(4):
                    pitch = n[(k + 2) % 3] - 12
                    self.note('brass', 'horns_marc', pitch, b0 + k, 0.9,
                              70, 0.09, pan=-0.2, send=0.5, ch=0)

    def sec_C1(self, S):
        p = self.p
        lg = p.get('lead_gain', 1.0)
        pg = p.get('perc_gain', 1.0)
        ck = p.get('climax', 1.0)
        d = p.get('density', 1.0)
        self.chord_pad('strings', 'strings_all', 4, 0, 20, 'string_pad', vel=88, gain=0.38)
        self.tremolo_pad('strings', 4, 0, 20, [-12, 0, 12], vel=90, gain=0.22)
        self.string_ostinato(4, 0, 20, vel=94, gain=0.32)
        # ★ 铜管齐奏主旋律
        self.melody('trumpets', S, 0.95 * lg * ck, 104, bus='lead', ch=0)
        self.melody('horns', S, 0.42 * ck, 98, octave=-1, bus='brass', with_pickup=False)
        self.melody('trombones', S, 0.38 * ck, 94, octave=-1, bus='brass', with_pickup=False)
        self.low_brass_ostinato(4, 0, 20, vel=96, gain=0.70 * ck, pattern='eighths')
        # 电子低音层（Zimmer hybrid：与低音铜管叠加，不是二选一）
        for bar in range(0, 20, 2):
            name = chord_at(4, bar)
            self.sub_bass(S + bar * 4, 8, midi_to_freq(CHORDS[name][1]), 0.55, 0.16)
        self.harp_arp(4, 0, 20, vel=0.8, gain=0.08)
        # 打击乐：结构声部
        for bar in range(20):
            self.timpani(S + bar * 4, 100, 0.34, note=self.timp_note(4, bar))
            self.bass_drum(S + bar * 4, 100, 0.32 * pg)
            for k in range(8 if p.get('c1_snare16', False) else 4):
                self.snare(S + bar * 4 + k * (0.5 if p.get('c1_snare16', False) else 1.0),
                           62, 0.08 * pg)
            if bar % 4 == 0:
                self.crash(S + bar * 4, 100, 0.26 * pg)
        # ♭II（Db）抬升：铜管全奏（两段力度递进）+ 定音鼓滚奏 → 直接砸进 C2
        self.brass_stab(4, 20, 82, 0.44, kind='tutti', dur=3.7, inst='brass_all', send=0.45)
        self.brass_stab(4, 22, 106, 0.52, kind='tutti', dur=3.7, inst='brass_all', send=0.45)
        self.chord_pad('strings', 'strings_all', 4, 20, 24, 'string_pad', vel=92, gain=0.40)
        self.timp_roll(S + 80, 16, 55, 127, 0.32 * pg, step=0.25 * d)
        self.crash(S + 95.9, 115, 0.30 * pg)

    def sec_C2(self, S):
        p = self.p
        lg = p.get('lead_gain', 1.0)
        pg = p.get('perc_gain', 1.0)
        cg = p.get('choir_gain', 1.0)
        ck = p.get('climax', 1.0)
        d = p.get('density', 1.0)
        self.chord_pad('strings', 'strings_all', 5, 0, 20, 'string_pad', vel=100, gain=0.42)
        self.tremolo_pad('strings', 5, 0, 20, [-12, 0, 12], vel=100, gain=0.26)
        self.string_ostinato(5, 0, 20, vel=100, gain=0.38)
        # ★ 全铜管八度齐奏 + 合唱 + 木管高八度
        self.melody('trumpets', S, 1.05 * lg * ck, 112, bus='lead', ch=0)
        self.melody('horns', S, 0.48 * ck, 108, octave=-1, bus='brass', with_pickup=False)
        self.melody('trombones', S, 0.44 * ck, 106, octave=-1, bus='brass', with_pickup=False)
        self.melody('tuba', S, 0.26 * ck, 100, octave=-2, bus='low', with_pickup=False)
        self.melody('piccolo', S, 0.12 * ck, 96, octave=1, bus='lead', with_pickup=False)
        # 合唱（SSO + synth hybrid）
        self.chord_pad('choir', 'choir', 5, 0, 20, 'choir', vel=85, gain=0.26 * cg, ch=4)
        self.choir_synth_pad(5, 0, 20, vel=0.85, gain=0.10 * cg)
        self.low_brass_ostinato(5, 0, 20, vel=100, gain=0.82, pattern='eighths')
        if p.get('c2_triplet', False):
            self.low_brass_ostinato(5, 8, 16, vel=100, gain=0.55, pattern='triplet')
        for bar in range(0, 20, 2):
            name = chord_at(5, bar)
            self.sub_bass(S + bar * 4, 8, midi_to_freq(CHORDS[name][1]), 0.65, 0.20)
        self.harp_arp(5, 0, 20, vel=0.85, gain=0.07)
        # 全打击乐 + 电子 kick
        for bar in range(20):
            self.timpani(S + bar * 4, 110, 0.40, note=self.timp_note(5, bar))
            self.bass_drum(S + bar * 4, 115, 0.38 * pg)
            self.bass_drum(S + bar * 4 + 2, 85, 0.26 * pg)
            for k in range(8):
                self.snare(S + bar * 4 + k * 0.5, 62, 0.075 * pg)
            if bar % 2 == 0:
                self.crash(S + bar * 4, 105, 0.28 * pg)
            # 电子 kick（Zimmer hybrid）
            a = synth_bass_drum(vel=0.9 * pg)
            self.mx.add('perc', a[np.newaxis, :], S + bar * 4, gain=0.10,
                        send=0.15, send_kind='short', kick=True, midi=(2, 35, 0.5, 100))
        # 二次滚奏 + 尾部终止
        self.timp_roll(S + 76, 4, 80, 120, 0.30 * pg)
        # 尾部 cadence：G → Cm 全奏
        self.brass_stab(5, 19, 95, 0.45, kind='brass_harmony', dur=3.6, inst='brass_all')
        self.brass_stab(5, 20, 110, 0.55, kind='tutti', dur=15.5, inst='brass_all', send=0.45)
        self.chord_pad('strings', 'strings_all', 5, 20, 24, 'string_pad', vel=100, gain=0.42)
        self.crash(S + 80, 120, 0.34 * pg)
        self.bass_drum(S + 80, 120, 0.44 * pg)
        self.glock(S + 80, 84, 110, 0.16)

    def sec_outro1(self, S):
        p = self.p
        lg = p.get('lead_gain', 1.0)
        pg = p.get('perc_gain', 1.0)
        self.chord_pad('strings', 'strings_all', 6, 0, 24, 'string_pad', vel=58, gain=0.28)
        self.chord_pad('strings', 'celli', 6, 0, 24, 'string_low', vel=52, gain=0.30)
        self.chord_pad('brass', 'horns', 6, 0, 20, 'brass_harmony', vel=50, gain=0.16)
        # ★ 圆号回到主旋律（退潮）
        self.melody('horn', S, 0.46 * lg, 80, bus='lead', ch=0)
        self.harp_arp(6, 0, 24, vel=0.6, gain=0.09)
        for bar in range(24):
            self.timpani(S + bar * 4, 52, 0.16, note=self.timp_note(6, bar))
        # 铜管和声收拢
        self.brass_stab(6, 20, 72, 0.34, kind='tutti', dur=7.4, inst='brass_all', send=0.55)

    def sec_outro2(self, S):
        p = self.p
        lg = p.get('lead_gain', 1.0)
        pg = self.p.get('perc_gain', 1.0)
        self.chord_pad('strings', 'strings_all', 7, 0, 18, 'string_pad', vel=40, gain=0.18)
        self.chord_pad('strings', 'celli', 7, 0, 24, 'string_low', vel=36, gain=0.20)
        # 独奏小提琴 / 长笛回响
        self.melody_short(MAIN[:5], S, 'violin_solo', 0.28 * lg, 68, bus='lead',
                          prec_pickup=True, ch=0)
        self.melody_short(MAIN[:5], S + 32, 'flute', 0.10 * lg, 55, octave=1,
                          bus='lead', ch=0)
        self.harp_arp(7, 0, 16, vel=0.4, gain=0.07)
        for bar in (4, 12):
            self.timpani(S + bar * 4, 42, 0.14 * pg)
        # V（G）→ 终止：渐强
        self.brass_stab(7, 18, 78, 0.24, kind='brass_harmony', dur=3.7,
                        inst='brass_all', send=0.6)
        self.brass_stab(7, 19, 96, 0.32, kind='brass_harmony', dur=3.7,
                        inst='brass_all', send=0.6)
        self.timp_roll(S + 72, 8, 40, 115, 0.22 * pg)
        # 终止一击：Picardy third（C 大三和弦）
        self.final_hit(S + 80)

    def final_hit(self, beat):
        """最终全奏：C 大三和弦，铜管高八度齐奏 + 定音鼓/大鼓/钹 + 合唱。"""
        notes = [36, 48, 52, 55, 60, 64, 67, 72, 76, 79]
        for k, p in enumerate(notes):
            pan = 0.35 * (k / (len(notes) - 1) - 0.5) * 2
            self.note('brass', 'brass_all', p, beat, 11.0, 118, 0.55,
                      pan=pan, send=0.5, ch=0)
        self.note('low', 'tuba', 36, beat, 11.0, 118, 0.30, send=0.3, ch=1)
        for k, p in enumerate([48, 55, 64, 72]):
            self.note('strings', 'strings_all', p, beat, 11.0, 110, 0.28,
                      pan=0.2 * (k - 1.5), send=0.6, ch=3)
        self.chord_pad('choir', 'choir', 7, 20, 24, 'choir', vel=100, gain=0.30, ch=4)
        self.timpani(beat, 122, 0.55, note=36)
        self.bass_drum(beat, 122, 0.60)
        self.crash(beat, 122, 0.40)
        self.glock(beat, 84, 112, 0.22)
        self.timpani(beat + 1, 70, 0.20, note=36)

    # ---------------------------------------------------------- 时间轴
    def render_music(self):
        print('  [music] 8 段编排 ...', flush=True)
        for i, (name, fn) in enumerate([('Intro', self.sec_intro), ('A1', self.sec_A1),
                                        ('B', self.sec_B), ('A2', self.sec_A2),
                                        ('C1', self.sec_C1), ('C2', self.sec_C2),
                                        ('Outro1', self.sec_outro1),
                                        ('Outro2', self.sec_outro2)]):
            t0 = time.time()
            fn(i * SEC_LEN)
            print(f'    {name:7s} {time.time() - t0:5.1f}s', flush=True)

    def timp_note(self, sec, bar):
        """定音鼓按当前和弦根音（映射到 C2..C3 的可演奏区）。"""
        name = chord_at(sec, bar)
        return {'Cm': 36, 'Ab': 44, 'Fm': 41, 'G': 43, 'Db': 38, 'C': 36}[name]

    # ====================================================== 分轨处理
    def process_buses(self):
        p = self.p
        b = self.mx.buf
        tg = p.get('comp_scale', 1.0)
        # 铜管（含主旋律 bus）：去泥 + 去盒音 + 光泽 + 慢速胶水压缩
        for bus in ('brass', 'lead'):
            x = b[bus]
            x = hp(x, 80, 3)
            x = band_cut(x, 200, 400, -1.5)
            x = band_boost(x, 2000, 5000, 2.5 * p.get('presence', 1.0))
            x = shelf_boost(x, 5000, 3.5 * p.get('air', 1.0))
            if p.get('exciter_db') is not None:
                x = exciter(x, 5000, p['exciter_db'])
            x = compress_auto(x, ratio=2.0, attack_ms=30, release_ms=250,
                              target_gr_db=1.5 * tg)
            b[bus] = x
        # 低音层：不 HP，kick 侧链让路
        x = b['low']
        key = self.mx.kick
        x = sidechain(x, key, thresh_db=p.get('sc_thresh', -18.0),
                      ratio=p.get('sc_ratio', 3.0), attack_ms=5, release_ms=120,
                      max_duck_db=p.get('sc_duck', 5.0))
        x = compress_auto(x, ratio=2.0, attack_ms=20, release_ms=200, target_gr_db=1.0)
        b['low'] = x
        # 弦乐：去低频浑浊 + 少量空气
        x = b['strings']
        x = hp(x, 80, 2)
        x = band_cut(x, 150, 350, -2.0)
        x = shelf_boost(x, 4000, 1.5 * p.get('air', 1.0))
        if p.get('exciter_db') is not None:
            x = exciter(x, 4500, p['exciter_db'] - 4.0)
        x = compress_auto(x, ratio=1.5, attack_ms=40, release_ms=300, target_gr_db=1.0)
        b['strings'] = x
        # 打击乐：300–500 Hz 动态衰减，保住 60–100 Hz 与 3–6 kHz 脆度
        x = b['perc']
        x = dynamic_cut(x, 300, 500, -2.0, thresh_pct=80)
        x = hp(x, 28, 2)
        x = band_boost(x, 3000, 6000, 2.0)
        b['perc'] = x
        # 合唱
        x = b['choir']
        x = hp(x, 60, 2)
        x = band_cut(x, 300, 600, -1.5)
        x = shelf_boost(x, 4000, 1.0 * p.get('air', 1.0))
        b['choir'] = x

    def mix_down(self):
        p = self.p
        self.process_buses()
        # 混响：铜管/弦乐/合唱 长 IR；打击乐 短 IR
        ir_long = make_ir(p.get('rv_long', 3.1), 1.6, 1.1, 0.6, seed=7)
        ir_short = make_ir(p.get('rv_short', 1.45), 0.55, 0.45, 0.3, seed=11)
        wet_l = apply_ir(self.mx.send['long'], ir_long)
        wet_s = apply_ir(self.mx.send['short'], ir_short)
        # 爆发段混响更干（C2 的 wet 比 A1 低 ~25%）
        curve = wet_curve(p.get('c2_wet', 0.75))
        wl = p.get('wet_long', 0.55)
        ws = p.get('wet_short', 0.5)
        out = np.zeros((2, N), np.float32)
        gains = {'lead': p.get('lead_bus', 1.0), 'brass': p.get('brass_bus', 1.0),
                 'low': p.get('low_bus', 1.0), 'strings': p.get('strings_bus', 1.0),
                 'perc': p.get('perc_bus', 1.0), 'choir': p.get('choir_bus', 1.0)}
        for bus in BUSES:
            out += self.mx.buf[bus] * gains[bus]
        out += wet_l * (wl * curve)[None, :]
        out += wet_s * (ws * curve)[None, :]
        return out

    def save_stems(self, out_dir):
        d = os.path.join(out_dir, 'stems')
        os.makedirs(d, exist_ok=True)
        names = {'brass': 'brass.wav', 'low': 'low_brass_bass.wav',
                 'strings': 'strings.wav', 'perc': 'percussion.wav',
                 'choir': 'choir_hybrid.wav', 'lead': 'melody_lead.wav'}
        gains = {'lead': self.p.get('lead_bus', 1.0), 'brass': self.p.get('brass_bus', 1.0),
                 'low': self.p.get('low_bus', 1.0), 'strings': self.p.get('strings_bus', 1.0),
                 'perc': self.p.get('perc_bus', 1.0), 'choir': self.p.get('choir_bus', 1.0)}
        for bus, fn in names.items():
            sf.write(os.path.join(d, fn), (self.mx.buf[bus] * gains[bus]).T, SR,
                     subtype='FLOAT')

    # ====================================================== 主流程
    def run(self, out_dir, version_name='v1', write_stems=True):
        t_all = time.time()
        os.makedirs(out_dir, exist_ok=True)
        self.render_music()
        self.samp.save_cache()
        print(f'  [sampler] 命中 {self.samp.hits} / 新建 {self.samp.misses}', flush=True)

        mx = self.mix_down()
        peak = float(np.abs(mx).max())
        # 预母带电平：把峰值压到 ~1.8，避免母带限幅器过度挤压
        if peak > 1.8:
            g = 1.8 / peak
            mx *= g
            print(f'  [mix] 峰值 {peak:.2f} → 统一增益 {20 * math.log10(g):.1f} dB', flush=True)
        else:
            print(f'  [mix] 未母带峰值 {peak:.3f}', flush=True)
        premaster = np.clip(mx, -4, 4)

        pm_path = os.path.join(out_dir, 'premaster.wav')
        sf.write(pm_path, premaster.T, SR, subtype='FLOAT')
        print(f'  ✅ premaster.wav', flush=True)

        if write_stems:
            self.save_stems(out_dir)
            print(f'  ✅ stems/ 6 条分轨', flush=True)

        final, info = master_chain(premaster, target_lufs=self.p.get('target_lufs', -15.0),
                                   ceiling_db=self.p.get('ceiling_db', -1.0),
                                   fade_out=self.p.get('fade_out', 3.5),
                                   sat_drive=self.p.get('sat_drive', 1.0))

        # 时长必须 240 ± 2 s（这里严格 240.00 s）
        final = final[:, :N]
        if final.shape[1] < N:
            final = np.pad(final, ((0, 0), (0, N - final.shape[1])))

        fix = os.path.join(out_dir, 'epic_final.wav')
        sf.write(fix, final.T, SR, subtype='PCM_24')
        print(f'  ✅ epic_final.wav ({final.shape[1] / SR:.2f}s)', flush=True)

        midi_path = os.path.join(out_dir, 'epic_final.mid')
        build_midi(midi_path, self.mx.events)
        print(f'  ✅ epic_final.mid ({len(self.mx.events)} note events)', flush=True)

        spec_path = os.path.join(out_dir, 'spectrogram_final.png')
        bands = spectrogram_and_bands(final, spec_path)
        print(f'  ✅ spectrogram_final.png', flush=True)

        report_path = os.path.join(out_dir, 'loudness_report.txt')
        sec_db = section_rms(premaster)
        print('  [动态曲线] ' + ' '.join(f'{v:.1f}' for v in sec_db), flush=True)
        write_report(report_path, final, info, bands, self, version_name, sec_db)
        print(f'  ✅ loudness_report.txt', flush=True)
        print(f'  [done] {version_name} 总耗时 {time.time() - t_all:.0f}s', flush=True)
        return info, bands


# ============================================================ DSP 工具
def _sos(kind, freq, order=2):
    return butter(order, freq, kind, fs=SR, output='sos')


def hp(x, f, order=2):
    return sosfilt(_sos('high', f, order), x, axis=-1).astype(np.float32)


def lp(x, f, order=2):
    return sosfilt(_sos('low', f, order), x, axis=-1).astype(np.float32)


def _band(x, lo, hi, order=2):
    return sosfilt(_sos('band', [lo, hi], order), x, axis=-1).astype(np.float32)


def band_cut(x, lo, hi, db, order=2):
    """窄带衰减（用带通做减法，近似 peaking EQ）。"""
    band = _band(x, lo, hi, order)
    return (x - band * (1.0 - 10 ** (db / 20.0))).astype(np.float32)


def band_boost(x, lo, hi, db, order=2):
    band = _band(x, lo, hi, order)
    return (x + band * (10 ** (db / 20.0) - 1.0)).astype(np.float32)


def shelf_boost(x, fc, db, order=2):
    """高频 shelf：FC 以上整体抬升（SSO 采样偏暗，需要补"空气感"）。"""
    if abs(db) < 0.01:
        return x
    hi = hp(x, fc, order)
    return (x + hi * (10 ** (db / 20.0) - 1.0)).astype(np.float32)


def exciter(x, fc=5000, amount_db=-28.0, band=(1200, 5000)):
    """谐波激励器：把 1.2–5 kHz 的二次谐波推到 fc 以上，补 5–10 kHz 的"金属光泽"。

    SSO 采样在高频几乎没有能量（实测 5 kHz 以上 <0.1%），这是纯 EQ 补不出来的，
    只能用受控的非线性生成谐波（与商业 exciter 同一原理）。
    """
    b = _band(x, band[0], band[1], 2)
    h = (b * np.abs(b)).astype(np.float32)
    h = hp(h, fc, 3)
    # 用抽样估计 RMS，避免整段计算
    idx = np.arange(0, x.shape[-1], 64)
    rx = float(np.sqrt(np.mean(x[:, idx] ** 2)) + 1e-12)
    rh = float(np.sqrt(np.mean(h[:, idx] ** 2)) + 1e-12)
    h *= (rx * 10 ** (amount_db / 20.0)) / rh
    return (x + h).astype(np.float32)


def dynamic_cut(x, lo, hi, db, thresh_pct=80):
    """动态 EQ：带内能量高时才衰减（用于打击乐 300–500 Hz 与铜管的打架）。"""
    band = _band(x, lo, hi, 2)
    env = _follow(np.abs(band).max(axis=0), 20, 200) + 1e-9
    thr = np.percentile(env, thresh_pct)
    duck = np.clip(env / (thr + 1e-9), 0, 1) * (1.0 - 10 ** (db / 20.0))
    return (x - band * duck[None, :]).astype(np.float32)


def _follow(sig, attack_ms=5.0, release_ms=100.0):
    """峰值跟随器：快攻慢放（用两个一极点滤波器取 max，向量化）。"""
    a_a = math.exp(-1.0 / (SR * attack_ms / 1000.0))
    a_r = math.exp(-1.0 / (SR * release_ms / 1000.0))
    fast = lfilter([1 - a_a], [1, -a_a], sig)
    slow = lfilter([1 - a_r], [1, -a_r], sig)
    return np.maximum(fast, slow).astype(np.float32)


def compress(x, thresh_db, ratio, attack_ms, release_ms, makeup_db=0.0):
    s = np.max(np.abs(x), axis=0)
    env = _follow(s, attack_ms, release_ms) + 1e-9
    lvl = 20 * np.log10(env)
    over = np.maximum(0.0, lvl - thresh_db)
    gr_db = -over * (1.0 - 1.0 / ratio)
    g = (10 ** (gr_db / 20.0)) * (10 ** (makeup_db / 20.0))
    return (x * g[None, :]).astype(np.float32)


def compress_auto(x, ratio, attack_ms, release_ms, target_gr_db):
    """按信号电平自动选阈值，保证 gain reduction ≈ target_gr_db。"""
    s = np.max(np.abs(x), axis=0)
    env = _follow(s, 10, 200)
    lvl = 20 * np.log10(np.percentile(env, 92) + 1e-9)
    over = target_gr_db / max(1e-6, (1.0 - 1.0 / ratio))
    return compress(x, lvl - over, ratio, attack_ms, release_ms)


def sidechain(x, key, thresh_db=-18.0, ratio=3.0, attack_ms=5, release_ms=120,
              max_duck_db=5.0):
    env = _follow(np.abs(key), attack_ms, release_ms) + 1e-9
    lvl = 20 * np.log10(env)
    over = np.maximum(0.0, lvl - thresh_db)
    duck = np.minimum(max_duck_db, over * (1.0 - 1.0 / ratio))
    g = 10 ** (-duck / 20.0)
    return (x * g[None, :]).astype(np.float32)


def make_ir(dur=3.0, decay_low=1.6, decay_mid=1.1, decay_high=0.6, seed=42):
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    ir = np.zeros((2, n), np.float32)
    for ch in range(2):
        x = rng.standard_normal(n).astype(np.float32)
        ir[ch] = (lp(x, 400) * np.exp(-t / decay_low)
                  + _band(x, 400, 4000) * np.exp(-t / decay_mid) * 0.75
                  + hp(x, 4000) * np.exp(-t / decay_high) * 0.4)
        ir[ch] *= np.minimum(1, t / 0.01)
        ir[ch] /= np.sqrt(np.sum(ir[ch] ** 2)) + 1e-9
    return ir


def apply_ir(send, ir):
    out = np.zeros_like(send)
    for ch in range(2):
        out[ch] = fftconvolve(send[ch], ir[ch])[:N].astype(np.float32)
    return out


def wet_curve(c2_wet=0.75):
    """爆发段（C1 尾 + C2）混响更干，保住高频冲击力。"""
    c = np.ones(N, np.float32)
    b0 = int(464 * BEAT * SR)
    b1 = int(576 * BEAT * SR)
    c[b0:b1] = c2_wet
    # 平滑过渡 0.3 s
    k = int(0.3 * SR)
    ramp = np.linspace(1, c2_wet, k)
    c[b0:b0 + k] = ramp
    c[b1 - k:b1] = np.linspace(c2_wet, 1, k)
    return c


# ============================================================ 母带
def true_peak_db(x, block=262144):
    """True Peak：分块 4 倍过采样（块间 50% 重叠，忽略边缘 32 点），内存可控且与 ffmpeg 接近。"""
    peak = 0.0
    n = x.shape[1]
    step = block // 2
    for start in range(0, n, step):
        seg = x[:, start:start + block]
        if seg.shape[1] < 32:
            break
        up = resample_poly(seg.astype(np.float64), 4, 1, axis=1)
        core = up[:, 32:-32] if up.shape[1] > 96 else up
        peak = max(peak, float(np.abs(core).max()))
        if start + block >= n:
            break
    return 20 * math.log10(peak + 1e-12)


def loudness(x):
    import pyloudnorm as pyln
    global _METER
    if '_METER' not in globals() or _METER is None:
        _METER = pyln.Meter(SR)
    return _METER.integrated_loudness(np.asarray(x.T, dtype=np.float64))


_METER = None


def limit(x, ceiling_lin, lookahead_ms=6, release_ms=70):
    L = int(SR * lookahead_ms / 1000.0)
    pk = maximum_filter1d(np.max(np.abs(x), axis=0), size=2 * L + 1)
    g = np.minimum(1.0, ceiling_lin / np.maximum(pk, 1e-9))
    a = math.exp(-1.0 / (SR * release_ms / 1000.0))
    gs = lfilter([1 - a], [1, -a], g)
    g = np.minimum(g, gs).astype(np.float32)
    return (x * g[None, :]).astype(np.float32)


def master_chain(x, target_lufs=-15.0, ceiling_db=-1.0, fade_out=3.5, sat_drive=1.0):
    info = {}
    # ① 校正 EQ：20 Hz 高通（24 dB/oct）+ 2–4 kHz 轻微收 + 空气感
    x = hp(x, 20, 4)
    x = band_cut(x, 2000, 4000, -0.8)
    x = shelf_boost(x, 6000, 1.5)
    # ② 胶水压缩：GR ≤ 3 dB
    x = compress_auto(x, ratio=1.8, attack_ms=35, release_ms=250, target_gr_db=2.5)
    info['glue_gr_db'] = 2.5
    # ③ 谐波增强：轻饱和，THD ≈ 1–2%
    drive = sat_drive
    x = (np.tanh(x * drive) / drive).astype(np.float32)
    info['thd_pct'] = 100 * measured_thd(drive)
    # ④ 响度对齐 + ⑤ True Peak 限幅（迭代）
    ceil_lin = 10 ** (ceiling_db / 20.0)
    for it in range(3):
        cur = loudness(x)
        gain_db = target_lufs - cur
        y = limit(x * 10 ** (gain_db / 20.0), ceil_lin * 1.03)
        tp = true_peak_db(y)
        if tp > ceiling_db - 0.02:
            y = y * 10 ** ((ceiling_db - 0.02 - tp) / 20.0)
        x = y.astype(np.float32)
        info['iterations'] = it + 1
        if abs(loudness(x) - target_lufs) < 0.35:
            break
    # ⑥ 结尾自然衰减（3–4 s）
    fi, fo = int(0.35 * SR), int(fade_out * SR)
    x[:, :fi] *= np.linspace(0, 1, fi)[None, :]
    if fo > 0:
        x[:, -fo:] *= (np.linspace(1, 0, fo) ** 0.85)[None, :]
    info['lufs'] = loudness(x)
    info['true_peak'] = true_peak_db(x)
    info['sample_peak'] = 20 * math.log10(float(np.abs(x).max()) + 1e-12)
    return x, info


def measured_thd(drive):
    """用 1 kHz 正弦测饱和函数的谐波失真（只用于报告）。"""
    t = np.arange(int(SR * 0.5)) / SR
    s = np.sin(2 * np.pi * 1000 * t) * 0.5
    y = np.tanh(s * drive) / drive
    w = np.hanning(len(t))
    Y = np.abs(np.fft.rfft(y * w)) ** 2
    f0 = int(1000 * len(t) / SR)
    fund = Y[max(0, f0 - 3):f0 + 4].sum()
    harm = 0.0
    for h in range(2, 8):
        idx = f0 * h
        if idx < len(Y) - 4:
            harm += Y[idx - 3:idx + 4].sum()
    return float(np.sqrt(harm / max(fund, 1e-12)))


# ============================================================ 频谱 & 报告
def spectrogram_and_bands(x, png_path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    mono = x.mean(axis=0).astype(np.float64)
    bands = {}
    # Welch 能量（检查 60–120 / 300–500 / 2–5k / >10k）
    from scipy.signal import welch
    f, pxx = welch(mono, fs=SR, nperseg=8192)
    for name, (lo, hi) in [('50-100Hz', (50, 100)), ('60-120Hz', (60, 120)),
                           ('300-500Hz', (300, 500)), ('2-5kHz', (2000, 5000)),
                           ('10k-16kHz', (10000, 16000))]:
        sel = (f >= lo) & (f <= hi)
        bands[name] = float(10 * np.log10(np.mean(pxx[sel]) + 1e-30))
    fig, axs = plt.subplots(2, 1, figsize=(14, 9))
    axs[0].specgram(mono, NFFT=2048, Fs=SR, noverlap=1024, cmap='magma',
                    vmin=-140, vmax=-20)
    axs[0].set_ylim(20, 16000)
    axs[0].set_yscale('symlog')
    axs[0].set_title('epic_final.wav — spectrogram (dB)')
    axs[0].set_xlabel('time (s)')
    axs[0].set_ylabel('Hz')
    axs[1].semilogx(f, 10 * np.log10(pxx + 1e-30))
    axs[1].set_xlim(20, 20000)
    axs[1].set_title('average spectrum')
    axs[1].set_xlabel('Hz')
    axs[1].set_ylabel('dB')
    axs[1].grid(True, which='both', alpha=0.3)
    fig.tight_layout()
    fig.savefig(png_path, dpi=110)
    plt.close(fig)
    return bands


def section_rms(premaster):
    """各段 RMS（dBFS），用来客观检查"建立→升级→爆发→余响"的动态曲线。"""
    out = []
    for i in range(8):
        a = int(i * SEC_LEN * BEAT * SR)
        b = int((i + 1) * SEC_LEN * BEAT * SR)
        seg = premaster[:, a:b]
        rms = float(np.sqrt(np.mean(seg ** 2)) + 1e-12)
        out.append(20 * math.log10(rms))
    return out


def write_report(path, final, info, bands, orch, version_name, sec_db=None):
    dur = final.shape[1] / SR
    lines = [
        '================ 史诗交响配乐渲染报告 ================',
        f'版本: {version_name}',
        f'采样率: {SR} Hz   声道: 2   时长: {dur:.2f} s   BPM: {BPM}',
        '',
        '--- 测量命令 ---',
        '  python epic_engine.py  (内容: pyloudnorm.Meter(48000).integrated_loudness)',
        '  ffmpeg -i epic_final.wav -af loudnorm=print_format=json -f null -   (交叉验证)',
        '',
        '--- 响度 / 峰值 ---',
        f'  Integrated loudness : {info["lufs"]:.2f} LUFS   (目标 -16 ~ -14)',
        f'  True Peak           : {info["true_peak"]:.2f} dBTP  (上限 -1.0)',
        f'  Sample Peak         : {info["sample_peak"]:.2f} dBFS',
        f'  胶水压缩 GR        : {info.get("glue_gr_db", 0):.1f} dB (≤3)',
        f'  饱和 THD            : {info.get("thd_pct", 0):.2f} %  (目标 1–2)',
        f'  限幅迭代次数        : {info.get("iterations", 0)}',
        '',
        '--- 频谱检查（平均功率，dB）---',
    ]
    for k, v in bands.items():
        lines.append(f'  {k:10s}: {v:7.1f} dB')
    if sec_db:
        lines += ['', '--- 段落 RMS 曲线（dBFS，母带前）---']
        names = ['Intro', 'A1', 'B', 'A2', 'C1', 'C2', 'Outro1', 'Outro2']
        for nm, v in zip(names, sec_db):
            lines.append(f'  {nm:7s}: {v:7.1f} dB')
        peak_sec = int(np.argmax(sec_db))
        lines.append(f'  最响段: {names[peak_sec]}（应为 C2）')
    stem_dir = os.path.join(os.path.dirname(path), 'stems')
    lines += ['', '--- 分轨（stems/）---']
    if os.path.isdir(stem_dir):
        for fn in sorted(os.listdir(stem_dir)):
            p = os.path.join(stem_dir, fn)
            lines.append(f'  {fn:22s} {os.path.getsize(p) / 1e6:7.2f} MB')
    lufs = info['lufs']
    lines += [
        '',
        '--- 验收 ---',
        f'  时长 240±2s        : {"PASS" if abs(dur - 240) <= 2 else "FAIL"} ({dur:.2f}s)',
        f'  LUFS -16..-14      : {"PASS" if -16 <= lufs <= -14 else "FAIL"} ({lufs:.2f})',
        f'  TruePeak ≤ -1.0    : {"PASS" if info["true_peak"] <= -1.0 else "FAIL"} ({info["true_peak"]:.2f})',
        f'  50–100Hz 有能量    : {"PASS" if bands["50-100Hz"] > -100 else "FAIL"} ({bands["50-100Hz"]:.1f} dB)',
        f'  2–5kHz 有穿透力    : {"PASS" if bands["2-5kHz"] > -110 else "FAIL"} ({bands["2-5kHz"]:.1f} dB)',
        f'  分轨 ≥3 条非空     : {"PASS" if os.path.isdir(stem_dir) and len(os.listdir(stem_dir)) >= 3 else "FAIL"}',
    ]
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


# ============================================================ MIDI
def _vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


TPQ = 480
CH_PROGRAM = {0: 56, 1: 57, 2: 47, 3: 48, 4: 52}


def build_midi(path, events, bpm=BPM):
    """格式 1 多轨 MIDI：ch0 主旋律铜管 / ch1 低音铜管 / ch2 打击乐 / ch3 弦乐 / ch4 合唱。"""
    import struct
    tempo_us = int(60_000_000 / bpm)

    # 轨道 0：tempo map
    trk0 = bytearray()
    trk0 += _vlq(0) + bytes([0xFF, 0x51, 0x03]) + tempo_us.to_bytes(3, 'big')
    for sec in range(8):
        tick = int(sec * SEC_LEN * TPQ)
        label = f'sec{sec + 1}'.encode()
        trk0 += _vlq(tick if sec == 0 else SEC_LEN * TPQ)
        trk0 += bytes([0xFF, 0x06]) + _vlq(len(label)) + label
    trk0 += _vlq(0) + bytes([0xFF, 0x2F, 0x00])

    tracks = []
    for ch in range(5):
        name = f'ch{ch}'.encode()
        trk = bytearray()
        trk += _vlq(0) + bytes([0xFF, 0x03]) + _vlq(len(name)) + name
        trk += _vlq(0) + bytes([0xC0 | ch, CH_PROGRAM[ch]])
        evs = []
        for (beat, c, pitch, dur, vel) in events:
            if c != ch:
                continue
            s = int(round(beat * TPQ))
            e = int(round((beat + max(0.05, dur)) * TPQ))
            evs.append((s, 1, bytes([0x90 | ch, pitch & 0x7F, max(1, min(127, vel))])))
            evs.append((e, 0, bytes([0x80 | ch, pitch & 0x7F, 64])))
        evs.sort(key=lambda z: (z[0], z[1]))
        prev = 0
        for tick, _, data in evs:
            tick = max(tick, prev)
            trk += _vlq(tick - prev) + data
            prev = tick
        trk += _vlq(0) + bytes([0xFF, 0x2F, 0x00])
        tracks.append(trk)

    all_trks = [trk0] + tracks
    header = b'MThd' + struct.pack('>IHHH', 6, 1, len(all_trks), TPQ)
    body = b''.join(b'MTrk' + struct.pack('>I', len(t)) + bytes(t) for t in all_trks)
    with open(path, 'wb') as f:
        f.write(header + body)
