# -*- coding: utf-8 -*-
"""v1 —— 第一次可运行版本：8 段 → "建立–升级–爆发–余响" 四幕骨架

对应 RESEARCH_NOTES.md 的规则：
  - 主旋律铜管化（A1 圆号 → A2 小号 → C1 铜管齐奏 → C2 全铜管 + 合唱）
  - 低音铜管固定音型（A2 起）
  - 打击乐作为结构声部
  - C1 尾部 Db 抬升 → C2 爆发
  - 结尾 Picardy third 一击
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epic_engine import Orchestrator

PROFILE = dict(
    cache_name='notes_v1.npz',
    lead_gain=1.0, chord_gain=1.0, perc_gain=1.0, choir_gain=1.0,
    density=1.0, intro_gain=1.0,
    # bus 电平
    lead_bus=1.0, brass_bus=1.0, low_bus=1.0, strings_bus=1.0,
    perc_bus=1.0, choir_bus=1.0,
    # 混响
    rv_long=3.1, rv_short=1.45, wet_long=0.55, wet_short=0.5, c2_wet=0.75,
    # 母带
    target_lufs=-15.0, ceiling_db=-1.0, fade_out=3.5,
    presence=1.0, sc_duck=5.0, comp_scale=1.0,
)


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'renders', 'v1')
    eng = Orchestrator(PROFILE)
    info, bands = eng.run(out, 'v1')


if __name__ == '__main__':
    main()
