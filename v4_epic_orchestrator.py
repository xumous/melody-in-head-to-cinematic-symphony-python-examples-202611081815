# -*- coding: utf-8 -*-
"""v4 —— 动态落差与母带版

在 v3 基础上：
  1. 开场更安静（intro_gain 0.78）→ 让 C2 的相对冲击更大（建立–升级–爆发的落差）
  2. C1/C2 主旋律与低音铜管再抬 15%（climax 1.15）：同一旋律每出现一次，力度 +1 级
  3. 激励器提到 −20 dB（SSO 高频缺失需要更强的谐波补偿），5–10 kHz 才有"金属光泽"
  4. 母带目标 −14.5 LUFS（流媒体标准），混响衰减 3.3 s（大厅感）
  5. 胶水压缩目标 GR 2.8 dB（仍 ≤3 dB）
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epic_engine import Orchestrator
from v3_epic_orchestrator import PROFILE as BASE

PROFILE = dict(BASE, **dict(
    intro_gain=0.78,
    climax=1.15,
    exciter_db=-20.0,
    rv_long=3.3,
    wet_long=0.48,
    wet_short=0.45,
    target_lufs=-14.5,
    ceiling_db=-1.0,
    comp_scale=1.1,
))


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'renders', 'v4')
    eng = Orchestrator(PROFILE)
    eng.run(out, 'v4')


if __name__ == '__main__':
    main()
