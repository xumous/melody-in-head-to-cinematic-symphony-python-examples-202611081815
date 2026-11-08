# -*- coding: utf-8 -*-
"""用 ffmpeg loudnorm 交叉验证响度，并把结果追加到 loudness_report.txt。"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
wav = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'epic_final.wav')
rep = os.path.join(os.path.dirname(wav), 'loudness_report.txt')

cmd = ['ffmpeg', '-hide_banner', '-i', wav, '-af', 'loudnorm=print_format=json', '-f', 'null', '-']
out = subprocess.run(cmd, capture_output=True, text=True, errors='replace').stderr
m = re.search(r'\{[^{}]*"input_i".*?\}', out, re.S)
if not m:
    print('ffmpeg parse failed')
    print(out[-2000:])
    sys.exit(1)
d = json.loads(m.group(0))
block = [
    '',
    '--- ffmpeg loudnorm 交叉验证 ---',
    '  命令: ffmpeg -i epic_final.wav -af loudnorm=print_format=json -f null -',
    f'  input_i   (integrated) : {d["input_i"]} LUFS',
    f'  input_tp  (true peak)  : {d["input_tp"]} dBTP',
    f'  input_lra (loudness range): {d["input_lra"]} LU',
    f'  input_thresh           : {d["input_thresh"]}',
]
with open(rep, 'a', encoding='utf-8') as f:
    f.write('\n'.join(block) + '\n')
print('\n'.join(block))
