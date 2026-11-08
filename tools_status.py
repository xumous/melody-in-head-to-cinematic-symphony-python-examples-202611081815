# -*- coding: utf-8 -*-
"""列出每个采样乐器的加载状态与可演奏音域（用于确认 SSO 子集是否够用）。"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import epic_engine as E
from pysfizz import Synth

for name, rel in E.INST.items():
    p = os.path.join(E.SSO_ROOT, rel)
    if not os.path.exists(p):
        print(f'{name:16s} NO_SFZ')
        continue
    s = Synth(sample_rate=48000, block_size=256)
    ok = s.load_sfz_file(p)
    keys = s.playable_keys if ok else []
    rng = f'{min(keys)}..{max(keys)}' if keys else '-'
    print(f'{name:16s} {("OK" if ok else "FF"):2s} regions={len(keys):3d} range={rng}')
