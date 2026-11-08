# -*- coding: utf-8 -*-
"""v5 —— 最终交付版（好莱坞史诗交响）

v4 → v5 的最后打磨：
  1. A2 小号主旋律 +1.3 dB，让"圆号 → 小号 → 铜管齐奏 → 全铜管+合唱"的力度阶梯真正成立
  2. B 段铜管和声长音 +3 dB、A1 低音铜管长音 +1.5 dB：中段不再"空"
  3. 激励器 −17 dB：SSO 采样 5 kHz 以上能量不足，靠谐波补偿拿到"金属光泽"
  4. climax ×1.2：C1/C2 的铜管与固定音型再加一档
  5. 目标响度回到 −15.0 LUFS（区间中值），C2 混响 0.72（比 A1 干 28%）
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epic_engine import Orchestrator
from v4_epic_orchestrator import PROFILE as BASE

PROFILE = dict(BASE, **dict(
    exciter_db=-17.0,
    climax=1.20,
    presence=1.20,
    air=1.15,
    target_lufs=-15.0,
    c2_wet=0.72,
    perc_bus=2.30,
    lead_bus=2.90,
    strings_bus=0.68,
))


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'renders', 'v5')
    eng = Orchestrator(PROFILE)
    eng.run(out, 'v5')


if __name__ == '__main__':
    main()
