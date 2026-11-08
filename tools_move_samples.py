# -*- coding: utf-8 -*-
"""把误放在各乐器目录下的 Samples / Samples-looped 合并回 SSO 根目录。

原因：SSO 的 includes/*.sfz 里的 sample=../Samples/... 是相对"主 SFZ 目录"解析的，
采样真实位置在 SSO 根目录的 Samples/ 与 Samples-looped/。
"""
import os, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'soundfonts', 'Sonatina Symphonic Orchestra')


def merge(sub):
    src_root = None
    moved = 0
    for d in os.listdir(ROOT):
        p = os.path.join(ROOT, d)
        if not os.path.isdir(p):
            continue
        cand = os.path.join(p, sub)
        if not os.path.isdir(cand):
            continue
        dst_root = os.path.join(ROOT, sub)
        os.makedirs(dst_root, exist_ok=True)
        for base, dirs, files in os.walk(cand):
            rel = os.path.relpath(base, cand)
            target_dir = os.path.join(dst_root, rel) if rel != '.' else dst_root
            os.makedirs(target_dir, exist_ok=True)
            for fn in files:
                s = os.path.join(base, fn)
                t = os.path.join(target_dir, fn)
                if os.path.exists(t) and os.path.getsize(t) >= os.path.getsize(s):
                    os.remove(s)
                else:
                    if os.path.exists(t):
                        os.remove(t)
                    shutil.move(s, t)
                    moved += 1
        # 清空目录
        for base, dirs, files in os.walk(cand, topdown=False):
            try:
                os.rmdir(base)
            except OSError:
                pass
    print(f'{sub}: moved {moved} files')


if __name__ == '__main__':
    merge('Samples')
    merge('Samples-looped')
    for sub in ('Samples', 'Samples-looped'):
        p = os.path.join(ROOT, sub)
        n = sum(len(f) for _, _, f in os.walk(p)) if os.path.isdir(p) else 0
        print(f'{sub}: {n} files now')
