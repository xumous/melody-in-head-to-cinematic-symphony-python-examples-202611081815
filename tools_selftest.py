# -*- coding: utf-8 -*-
"""自检：用桩采样器（合成噪声替代 SSO）验证整条渲染链：编排→分轨→DSP→母带→MIDI→报告。

用途：在采样还没下完时先验证代码路径与内存/耗时，避免"第一次跑真采样才发现崩"。
"""
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import epic_engine as E


class StubSampler:
    def __init__(self, *a, **kw):
        self.hits = self.misses = 0

    def synth(self, inst):
        return None

    def note(self, inst, pitch, vel, on_dur, tail=0.35):
        self.misses += 1
        n = int((on_dur + tail) * E.SR)
        n = max(n, int(0.05 * E.SR))
        t = np.arange(n) / E.SR
        f = E.midi_to_freq(pitch)
        env = np.exp(-t / (tail + 0.2)) * np.minimum(1, t / 0.01)
        a = (np.sin(2 * np.pi * f * t) * 0.5
             + np.random.randn(n) * 0.03) * env
        y = np.stack([a, a]).astype(np.float32) * (0.5 + vel / 200.0)
        return y * 0.05

    def save_cache(self):
        pass


def main():
    E.Orchestrator.__init__.__defaults__  # noop
    eng = E.Orchestrator({'cache_name': 'x.npz'})
    eng.samp = StubSampler()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'renders', 'selftest')
    t0 = time.time()
    info, bands = eng.run(out, 'selftest')
    print('OK', info, bands, f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
