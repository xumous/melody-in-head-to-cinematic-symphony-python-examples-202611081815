# -*- coding: utf-8 -*-
"""最小验证：pysfizz + SSO 渲染 C 大三和弦（小号/圆号/长号/大号）+ 一记定音鼓 → probe.wav。

任务书 §2.2 要求：只有 probe.wav 听起来像真实铜管/定音鼓，才继续往下做。
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import soundfile as sf
import epic_engine as E

SR = E.SR
HERE = os.path.dirname(os.path.abspath(__file__))
samp = E.Sampler(cache_path=None)


def place(buf, audio, start):
    n = min(audio.shape[1], buf.shape[1] - start)
    if n > 0:
        buf[:, start:start + n] += audio[:, :n]


def main():
    dur = 7.0
    buf = np.zeros((2, int(dur * SR)), np.float32)
    tones = [60, 64, 67, 72]
    for i, p in enumerate(tones):
        for inst, off, gain in [('trumpets', 0, 0.32), ('horns', -12, 0.26),
                                ('trombones', -12, 0.24), ('tuba', -24, 0.26)]:
            a = samp.note(inst, p + off, 110, 1.2, 1.6) * gain
            place(buf, a, int((0.1 + i * 0.03) * SR))
    # 定音鼓一击
    a = samp.note('timpani', 36, 120, 0.14, 1.4) * 0.5
    place(buf, a, int(2.4 * SR))
    # 小军鼓 + 大鼓
    d = samp.note('drumkit', E.PERC['bass_drum'], 115, 0.12, 1.0) * 0.4
    place(buf, d, int(3.6 * SR))
    sn = samp.note('drumkit', E.PERC['snare'], 110, 0.1, 0.6) * 0.25
    place(buf, sn, int(3.9 * SR))
    # 弦乐 tremolo
    t = samp.note('tremolo', 60, 100, 1.0, 1.0) * 0.2
    place(buf, t, int(4.6 * SR))
    # 合唱
    c = samp.note('choir', 60, 100, 1.0, 1.2) * 0.2
    place(buf, c, int(5.4 * SR))

    buf = buf / (np.abs(buf).max() + 1e-9) * 0.92
    sf.write(os.path.join(HERE, 'probe.wav'), buf.T, SR, subtype='PCM_16')
    print('probe.wav written', buf.shape)


if __name__ == '__main__':
    main()
