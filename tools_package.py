# -*- coding: utf-8 -*-
"""把最终版本的产物拷到 epic_rebuild 根目录，并做最终验收检查。"""
import os, shutil, sys
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
PICK = sys.argv[1] if len(sys.argv) > 1 else 'v5'
SRC = os.path.join(HERE, 'renders', PICK)

FILES = ['epic_final.wav', 'epic_final.mid', 'premaster.wav',
         'loudness_report.txt', 'spectrogram_final.png']


def main():
    if not os.path.isdir(SRC):
        raise SystemExit(f'missing {SRC}')
    for fn in FILES:
        s = os.path.join(SRC, fn)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(HERE, fn))
            print('copied', fn)
    stem_src = os.path.join(SRC, 'stems')
    stem_dst = os.path.join(HERE, 'stems')
    os.makedirs(stem_dst, exist_ok=True)
    for fn in sorted(os.listdir(stem_src)):
        shutil.copy2(os.path.join(stem_src, fn), os.path.join(stem_dst, fn))
        print('copied stems/' + fn)

    x, sr = sf.read(os.path.join(HERE, 'epic_final.wav'))
    print(f'final: {x.shape} {sr}Hz  {x.shape[0] / sr:.2f}s')


if __name__ == '__main__':
    main()
