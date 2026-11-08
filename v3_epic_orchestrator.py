# -*- coding: utf-8 -*-
"""v3 —— 亮度与织体强化版

在 v2 基础上：
  1. SSO 采样 5 kHz 以上几乎无能量（实测 <0.1%），纯 EQ 补不出来 →
     铜管/主旋律加谐波激励（exciter −26 dB，5 kHz 以上），弦乐 −30 dB
  2. presence +2.5 dB → ×1.15，air ×1.1
  3. 电平再平衡：主旋律 +1.3 dB（lead 2.8），打击乐 +1.8 dB（2.2），弦乐 −0.5 dB
  4. A2 加圆号对位声部；C2 中段低音铜管改三连音固定音型；C1 小军鼓改 16 分
  5. 打击乐/合唱密度 +15%，只作用在升级与爆发段
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epic_engine import Orchestrator
from v2_epic_orchestrator import PROFILE as BASE

PROFILE = dict(BASE, **dict(
    presence=1.15,
    air=1.10,
    exciter_db=-26.0,
    lead_bus=2.80,
    brass_bus=1.50,
    strings_bus=0.70,
    low_bus=0.98,
    perc_bus=2.20,
    choir_bus=1.60,
    a2_counter=True,
    c2_triplet=True,
    c1_snare16=True,
    density=1.15,
    perc_gain=1.15,
    choir_gain=1.15,
    c2_wet=0.68,
))


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'renders', 'v3')
    eng = Orchestrator(PROFILE)
    eng.run(out, 'v3')


if __name__ == '__main__':
    main()
