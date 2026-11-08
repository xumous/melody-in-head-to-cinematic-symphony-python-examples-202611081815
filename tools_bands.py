# -*- coding: utf-8 -*-
"""分轨频段分布诊断（找高频丢失的根源）。"""
import os, sys
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
BANDS = [(20, 60), (60, 120), (120, 300), (300, 500), (500, 1200),
         (1200, 2500), (2500, 5000), (5000, 10000), (10000, 20000)]


def band_pct(x):
    mono = x.mean(axis=1)
    S = np.abs(np.fft.rfft(mono)) ** 2
    f = np.fft.rfftfreq(len(mono), 1 / 48000)
    tot = S.sum() + 1e-20
    return [100 * S[(f >= lo) & (f < hi)].sum() / tot for lo, hi in BANDS]


def main(d):
    base = os.path.join(HERE, d)
    print('band%: ' + ' '.join(f'{lo}-{hi}' for lo, hi in BANDS))
    for fn in sorted(os.listdir(os.path.join(base, 'stems'))):
        x, sr = sf.read(os.path.join(base, 'stems', fn))
        p = band_pct(x)
        print(f'{fn:22s} ' + ' '.join(f'{v:6.1f}' for v in p))
    x, sr = sf.read(os.path.join(base, 'epic_final.wav'))
    p = band_pct(x)
    print(f'{"final":22s} ' + ' '.join(f'{v:6.1f}' for v in p))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'renders/v1')
