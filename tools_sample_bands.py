# -*- coding: utf-8 -*-
"""直接分析 SSO 采样文件的频谱，判断是库本身偏暗还是渲染链偏暗。"""
import os, glob
import numpy as np
import soundfile as sf

ROOT = 'D:/_sso'
BANDS = [(20, 60), (60, 120), (120, 300), (300, 500), (500, 1200),
         (1200, 2500), (2500, 5000), (5000, 10000), (10000, 20000)]


def pct(x, sr):
    S = np.abs(np.fft.rfft(x.mean(axis=1) if x.ndim == 2 else x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / sr)
    tot = S.sum() + 1e-20
    return [100 * S[(f >= lo) & (f < hi)].sum() / tot for lo, hi in BANDS]


files = []
for pat in ['Samples/Trumpets/*.wav', 'Samples-looped/Trumpets/*.wav',
            'Samples/Horns/*.wav', 'Samples/Trombones/*.wav',
            'Samples/1st Violins/*.wav', 'Samples/Celli/*.wav']:
    files += glob.glob(os.path.join(ROOT, pat))[:2]

print('band%: 20-60 60-120 120-300 300-500 500-1.2k 1.2-2.5k 2.5-5k 5-10k 10-20k')
for f in files:
    x, sr = sf.read(f, frames=48000)
    if x.ndim == 2:
        x = x[:, :1]
    print(f'{os.path.basename(f):40s} SR={sr} ' + ' '.join(f'{v:5.1f}' for v in pct(x, sr)))
