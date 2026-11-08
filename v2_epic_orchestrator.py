# -*- coding: utf-8 -*-
"""v2 —— 频谱与平衡修正版

v1 客观诊断（tools_diagnose.py / tools_bands.py）暴露的问题与修正：
  1. 2.5 kHz 以上能量几乎为 0（SSO 采样本身偏暗）→ 铜管/主旋律加 2–5 kHz presence +2.5 dB、
     5 kHz 以上 air +3.5 dB；弦乐加 4 kHz +1.5 dB；母带加 6 kHz shelf +1.5 dB
  2. 主旋律被弦乐压住（melody_lead −43.6 dB vs strings −35.2 dB）→ lead bus +7.6 dB，
     strings bus −2.5 dB
  3. 打击乐太轻（−43 dB）→ perc bus +5.1 dB
  4. 弦乐 120–300 Hz 占比 59.5%（低频浑浊）→ HP 80 Hz + 150–350 Hz −2 dB 窄带衰减
  5. THD 2.43% 超出 1–2% → 饱和驱动降到 1.0（实测 1.96%）
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epic_engine import Orchestrator
from v1_epic_orchestrator import PROFILE as BASE

PROFILE = dict(BASE, **dict(
    cache_name='notes_v1.npz',
    # 频谱
    presence=1.0, air=1.0,
    # bus 电平（相对 v1）
    lead_bus=2.40,  # +7.6 dB
    strings_bus=0.75,  # −2.5 dB
    brass_bus=1.35,
    perc_bus=1.80,  # +5.1 dB
    choir_bus=1.50,
    low_bus=1.05,
    # 混音
    sc_duck=6.5, sc_ratio=3.2,
    c1_snare16=True,
    c2_wet=0.70,
    comp_scale=1.2,
    wet_long=0.50,
    sat_drive=1.0,
))


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'renders', 'v2')
    eng = Orchestrator(PROFILE)
    eng.run(out, 'v2')


if __name__ == '__main__':
    main()
