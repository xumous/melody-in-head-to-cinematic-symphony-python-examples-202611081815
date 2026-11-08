# -*- coding: utf-8 -*-
"""定位高频丢失环节：分别测试 原始采样 / bus 处理 / 母带链 的频谱。"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import epic_engine as E

BANDS = [(20, 60), (60, 120), (120, 300), (300, 500), (500, 1200),
         (1200, 2500), (2500, 5000), (5000, 10000), (10000, 20000)]


def pct(x):
    mono = x.mean(axis=0) if x.ndim == 2 else x
    S = np.abs(np.fft.rfft(mono)) ** 2
    f = np.fft.rfftfreq(len(mono), 1 / E.SR)
    tot = S.sum() + 1e-20
    return [100 * S[(f >= lo) & (f < hi)].sum() / tot for lo, hi in BANDS]


def show(tag, x):
    print(f'{tag:24s} ' + ' '.join(f'{v:5.1f}' for v in pct(x)))


samp = E.Sampler(cache_path=None)
a = samp.note('trumpets', 67, 100, 0.6, 0.3)
show('raw trumpet', a)

noise = np.random.randn(2, E.SR).astype(np.float32) * 0.1
show('white noise', noise)

b = E.hp(noise, 80, 3)
show('hp80', b)
c = E.band_cut(b, 200, 400, -1.5)
show('band_cut200-400', c)
d = E.band_boost(c, 2000, 5000, 1.0)
show('band_boost2-5k', d)
e = E.compress_auto(d, ratio=2.0, attack_ms=30, release_ms=250, target_gr_db=1.5)
show('compress_auto', e)
m, info = E.master_chain(e * 3, target_lufs=-15, ceiling_db=-1, fade_out=0.0)
show('master_chain', m)
print(info)
