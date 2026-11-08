# -*- coding: utf-8 -*-
"""检查 probe.wav：各乐器段落是否有能量、频谱质心是否合理（证明是采样而非正弦）。"""
import numpy as np
import soundfile as sf

x, SR = sf.read('probe.wav')
print(f'dur {len(x) / SR:.2f}s  peak {np.abs(x).max():.3f}')
segs = [('brass chord', 0.0, 2.3), ('timpani', 2.4, 3.5), ('bass drum', 3.6, 3.9),
        ('snare', 3.9, 4.4), ('tremolo', 4.6, 5.3), ('choir', 5.4, 6.4)]
for name, a, b in segs:
    seg = x[int(a * SR):int(b * SR)]
    rms = float(np.sqrt((seg ** 2).mean()))
    pk = float(np.abs(seg).max())
    mono = seg.mean(axis=1) * np.hanning(len(seg))
    S = np.abs(np.fft.rfft(mono))
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    cen = float((S * f).sum() / (S.sum() + 1e-9))
    bands = [(0, 200), (200, 1000), (1000, 4000), (4000, 12000)]
    e = [float(S[(f >= lo) & (f < hi)].sum()) for lo, hi in bands]
    tot = sum(e) + 1e-9
    pct = [f'{100 * v / tot:.0f}%' for v in e]
    print(f'{name:12s} rms={rms:.4f} peak={pk:.3f} centroid={cen:6.0f}Hz  '
          f'band 0-200/200-1k/1-4k/4-12k = {"/".join(pct)}')
