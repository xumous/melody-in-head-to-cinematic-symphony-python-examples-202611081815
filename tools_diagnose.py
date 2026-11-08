# -*- coding: utf-8 -*-
"""诊断：分轨电平、段落动态、频段分布。"""
import os, sys
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
SEC = 30.0


def rms_db(x):
    return 20 * np.log10(float(np.sqrt(np.mean(x ** 2)) + 1e-12))


def main(d='renders/v1'):
    base = os.path.join(HERE, d)
    print('== stems ==')
    for fn in sorted(os.listdir(os.path.join(base, 'stems'))):
        x, sr = sf.read(os.path.join(base, 'stems', fn))
        if x.ndim == 1:
            x = np.stack([x, x], axis=1)
        print(f'{fn:22s} dur={len(x) / sr:6.2f}s peak={np.abs(x).max():.3f} rms={rms_db(x):6.1f}dB')
        # 段落
        per = []
        for i in range(8):
            seg = x[int(i * SEC * sr):int((i + 1) * SEC * sr)]
            per.append(rms_db(seg))
        print('   sections: ' + ' '.join(f'{v:.1f}' for v in per))

    print('\n== final ==')
    x, sr = sf.read(os.path.join(base, 'epic_final.wav'))
    print(f'peak={np.abs(x).max():.3f} rms={rms_db(x):.1f}')

    # 频段
    mono = x.mean(axis=1)
    S = np.abs(np.fft.rfft(mono * np.hanning(len(mono)))
               if False else np.fft.rfft(mono))
    f = np.fft.rfftfreq(len(mono), 1 / sr)
    bands = [(20, 60), (60, 120), (120, 300), (300, 500), (500, 1200),
             (1200, 2500), (2500, 5000), (5000, 10000), (10000, 20000)]
    tot = (S ** 2).sum()
    for lo, hi in bands:
        e = (S[(f >= lo) & (f < hi)] ** 2).sum()
        print(f'  {lo:5d}-{hi:5d}Hz: {100 * e / tot:5.2f}%')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'renders/v1')
