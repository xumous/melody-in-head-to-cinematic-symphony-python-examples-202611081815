# -*- coding: utf-8 -*-
"""按需抓取 SSO 的 SFZ + 采样（只下史诗配乐真正要用的乐器）。

策略：并行抓取（镜像单请求延迟不稳定，串行会被单个卡死）。
目录结构与仓库一致，sfizz 才能按相对路径找到采样。
"""
import os, re, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, 'soundfonts', 'Sonatina Symphonic Orchestra')
PROXY = 'https://gh-proxy.com/https://raw.githubusercontent.com/peastman/sso/master/'
REPO_PREFIX = 'Sonatina Symphonic Orchestra/'

WANT = [
    'Brass - Notation/All Brass Sustain.sfz',
    'Brass - Notation/All Brass Marcato.sfz',
    'Brass - Notation/All Brass Staccato.sfz',
    'Brass - Notation/Horn Solo Sustain (looped).sfz',
    'Brass - Notation/Horn Solo Sustain.sfz',
    'Brass - Notation/Horn Solo Marcato (looped).sfz',
    'Brass - Notation/Horn Solo Marcato (looped, decay).sfz',
    'Brass - Notation/Horn Solo Staccato.sfz',
    'Brass - Notation/Horns Sustain.sfz',
    'Brass - Notation/Horns Marcato.sfz',
    'Brass - Notation/Horns Staccato.sfz',
    'Brass - Notation/Horns Legato.sfz',
    'Brass - Notation/Trumpet Solo Sustain (looped).sfz',
    'Brass - Notation/Trumpet Solo Marcato (looped).sfz',
    'Brass - Notation/Trumpet Solo Staccato.sfz',
    'Brass - Notation/Trumpet Solo Legato.sfz',
    'Brass - Notation/Trumpets Sustain.sfz',
    'Brass - Notation/Trumpets Marcato.sfz',
    'Brass - Notation/Trumpets Staccato.sfz',
    'Brass - Notation/Trombones Sustain.sfz',
    'Brass - Notation/Trombones Marcato.sfz',
    'Brass - Notation/Trombones Staccato.sfz',
    'Brass - Notation/Bass Trombone Solo Sustain (looped).sfz',
    'Brass - Notation/Bass Trombone Solo Marcato (looped).sfz',
    'Brass - Notation/Tuba Sustain.sfz',
    'Brass - Notation/Tuba Staccato.sfz',
    'Brass - Notation/Tuba Marcato.sfz',
    'Strings - Notation/All Strings Sustain.sfz',
    'Strings - Notation/All Strings Tremolo.sfz',
    'Strings - Notation/All Strings Marcato.sfz',
    'Strings - Notation/All Strings Staccato.sfz',
    'Strings - Notation/Celli Sustain.sfz',
    'Strings - Notation/Celli Marcato.sfz',
    'Strings - Notation/Celli Staccato.sfz',
    'Strings - Notation/Basses Sustain.sfz',
    'Strings - Notation/Basses Marcato.sfz',
    'Strings - Notation/Violas Sustain.sfz',
    'Strings - Notation/Violas Tremolo.sfz',
    'Strings - Notation/Violas Marcato.sfz',
    'Strings - Notation/1st Violins Sustain.sfz',
    'Strings - Notation/1st Violins Tremolo.sfz',
    'Strings - Notation/1st Violins Marcato.sfz',
    'Strings - Notation/Violin Solo 1 Sustain (looped).sfz',
    'Strings - Notation/Violin Solo 1 Marcato (looped).sfz',
    'Woodwinds - Notation/All Woodwinds Sustain.sfz',
    'Woodwinds - Notation/Flute Solo 1 Sustain (looped).sfz',
    'Woodwinds - Notation/Flute Solo 1 Marcato (looped).sfz',
    'Woodwinds - Notation/Oboe Solo Sustain (looped).sfz',
    'Woodwinds - Notation/Oboe Solo Marcato (looped).sfz',
    'Woodwinds - Notation/Bassoon Solo Sustain (looped).sfz',
    'Woodwinds - Notation/Bassoons Sustain.sfz',
    'Woodwinds - Notation/Piccolo Solo Sustain (looped).sfz',
    'Percussion/Timpani.sfz',
    'Percussion/Bass Drum & Snare.sfz',
    'Percussion/Cymbals & Tamtam.sfz',
    'Percussion/Glockenspiel.sfz',
    'Percussion/Triangle.sfz',
    'Chorus - Notation/Mixed Chorus.sfz',
    'Chorus - Notation/Large Chrous.sfz',
]


def url_for(relpath):
    return PROXY + urllib.parse.quote(REPO_PREFIX + relpath, safe='/')


def fetch_text(relpath, retries=4):
    for i in range(retries):
        try:
            req = urllib.request.Request(url_for(relpath), headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=12) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception:
            time.sleep(0.6 + i)
    return None


def fetch_level(paths, workers=12):
    """并行抓取一批文本，返回 {path: text}"""
    out = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch_text, p): p for p in paths}
        for fut in as_completed(futs):
            p = futs[fut]
            txt = fut.result()
            if txt:
                out[p] = txt
    return out


def main():
    t0 = time.time()
    texts = {}
    level = list(WANT)
    print(f'level0: {len(level)} sfz', flush=True)
    got = fetch_level(level)
    texts.update(got)
    print(f'  got {len(got)}/{len(level)} in {time.time() - t0:.0f}s', flush=True)

    # 递归 include
    for depth in range(3):
        need = set()
        for rel, txt in texts.items():
            base = os.path.dirname(rel)
            for m in re.finditer(r'#include\s+"([^"]+)"', txt):
                inc = os.path.normpath(os.path.join(base, m.group(1))).replace('\\', '/')
                if inc not in texts:
                    need.add(inc)
        if not need:
            break
        need = sorted(need)
        print(f'level{depth + 1}: {len(need)} includes', flush=True)
        got = fetch_level(need)
        texts.update(got)
        print(f'  got {len(got)}/{len(need)}', flush=True)

    # 写 SFZ
    for rel, txt in texts.items():
        dst = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(txt)

    # 收集 sample 路径
    samples = set()
    for rel, txt in texts.items():
        base = os.path.dirname(rel)
        for m in re.finditer(r'sample=([^\s\r\n]+)', txt):
            sp = m.group(1).strip()
            if sp.startswith('*'):
                continue
            samples.add(os.path.normpath(os.path.join(base, sp)).replace('\\', '/'))
    print(f'SFZ {len(texts)} 个，采样 {len(samples)} 个', flush=True)

    def dl(rel, retries=5):
        dst = os.path.join(ROOT, rel)
        if os.path.exists(dst) and os.path.getsize(dst) > 1000:
            return 'skip'
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        for i in range(retries):
            try:
                req = urllib.request.Request(url_for(rel), headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=25) as r:
                    data = r.read()
                if len(data) < 1000:
                    raise IOError('too small')
                tmp = dst + '.part'
                with open(tmp, 'wb') as f:
                    f.write(data)
                os.replace(tmp, dst)
                return 'ok'
            except Exception:
                time.sleep(0.8 + i)
        return 'fail'

    todo = sorted(samples)
    ok = skip = fail = 0
    t1 = time.time()
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(dl, r): r for r in todo}
        for k, fut in enumerate(as_completed(futs)):
            st = fut.result()
            ok += st == 'ok'
            skip += st == 'skip'
            fail += st == 'fail'
            if (k + 1) % 30 == 0:
                print(f'  {k + 1}/{len(todo)} ok={ok} skip={skip} fail={fail} '
                      f'{time.time() - t1:.0f}s', flush=True)
    print(f'采样完成 ok={ok} skip={skip} fail={fail}', flush=True)

    if fail:
        bad = [r for r in todo if not (os.path.exists(os.path.join(ROOT, r)) and
                                       os.path.getsize(os.path.join(ROOT, r)) > 1000)]
        print(f'重试 {len(bad)} 个', flush=True)
        for k, r in enumerate(bad):
            st = dl(r, retries=8)
            if st == 'fail':
                print('  FAIL', r, flush=True)
        print('重试完成', flush=True)


if __name__ == '__main__':
    main()
