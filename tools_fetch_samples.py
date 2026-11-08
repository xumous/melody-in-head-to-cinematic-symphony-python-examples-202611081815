# -*- coding: utf-8 -*-
"""SSO 采样下载器（requests 连接池 + 断点续传 + 优先级）。

镜像 gh-proxy.com 单连接 ~20-170 kB/s，握手成本高，因此：
  - 复用 Session（keep-alive）避免每次 TLS 握手
  - 12 并发 + 每个文件 6 次重试（Range 续传）
  - 按优先级排序：Percussion → Brass → Strings → Woodwinds → Chorus
"""
import os, re, time, json
import requests
from requests.adapters import HTTPAdapter
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, 'soundfonts', 'Sonatina Symphonic Orchestra')
PROXY_BASES = (
    'https://gcore.jsdelivr.net/gh/peastman/sso@master/',
    'https://testingcf.jsdelivr.net/gh/peastman/sso@master/',
    'https://fastly.jsdelivr.net/gh/peastman/sso@master/',
    'https://gh-proxy.com/https://raw.githubusercontent.com/peastman/sso/master/',
    'https://gh-proxy.com/raw.githubusercontent.com/peastman/sso/master/',
)
PROXY = PROXY_BASES[0]
REPO_PREFIX = 'Sonatina Symphonic Orchestra/'
SAMPLE_LIST = os.path.join(HERE, 'logs', 'sample_list.json')


def url_for(rel, variant=0):
    base = PROXY_BASES[variant % len(PROXY_BASES)]
    return base + quote(REPO_PREFIX + rel, safe='/')


def session():
    s = requests.Session()
    ad = HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=0)
    s.mount('https://', ad)
    s.headers.update({'User-Agent': 'Mozilla/5.0'})
    return s


def collect_samples():
    """只收集 epic_engine 里实际会加载的音色所引用的采样（减少 40%+ 流量）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'epic_engine_local', os.path.join(HERE, 'epic_engine.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    inst = mod.INST

    samples = set()
    for rel_sfz in inst.values():
        p = os.path.join(ROOT, rel_sfz)
        if not os.path.exists(p):
            continue
        # 关键：SSO 的 include 文件里的 sample=../Samples/... 是相对"主 SFZ 目录"解析的
        owner_dir = os.path.dirname(rel_sfz).replace('\\', '/')
        queue = [rel_sfz]
        seen = set()
        while queue:
            rel = queue.pop()
            if rel in seen:
                continue
            seen.add(rel)
            fp = os.path.join(ROOT, rel)
            if not os.path.exists(fp):
                continue
            txt = open(fp, encoding='utf-8', errors='replace').read()
            for m in re.finditer(r'#include\s+"([^"]+)"', txt):
                inc = os.path.normpath(os.path.join(os.path.dirname(rel), m.group(1)))
                queue.append(inc.replace('\\', '/'))
            for m in re.finditer(r'sample=([^\s\r\n]+)', txt):
                sp = m.group(1).strip()
                if sp.startswith('*'):
                    continue
                samples.add(os.path.normpath(os.path.join(owner_dir, sp)).replace('\\', '/'))
    return samples


def priority(rel):
    fams = ['Percussion', 'Brass', 'Strings', 'Woodwinds', 'Chorus']
    fi = 99
    for i, k in enumerate(fams):
        if f'/{k}/' in rel or rel.startswith(f'Samples-looped/{k}'):
            fi = i
            break
    sustain = 0 if ('Sustain' in rel or 'looped' in rel or 'sustain-looped' in rel) else 1
    return (fi, sustain, rel)


def download(rel, sess, retries=4, variant0=0):
    dst = os.path.join(ROOT, rel)
    if os.path.exists(dst) and os.path.getsize(dst) > 1000:
        return 'skip'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + '.part'
    for i in range(retries):
        have = os.path.getsize(tmp) if os.path.exists(tmp) else 0
        headers = {'Range': f'bytes={have}-'} if have else {}
        try:
            r = sess.get(url_for(rel, variant0 + i), headers=headers, timeout=(10, 45), stream=True)
            if r.status_code not in (200, 206):
                r.close()
                time.sleep(1 + i)
                continue
            mode = 'ab' if (have and r.status_code == 206) else 'wb'
            if mode == 'wb':
                have = 0
            total = int(r.headers.get('Content-Length') or 0)
            with open(tmp, mode) as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk)
                    have += len(chunk)
            r.close()
            size_ok = (total == 0 and have > 1000) or (total > 0 and have >= total)
            if size_ok:
                os.replace(tmp, dst)
                return 'ok'
        except Exception:
            time.sleep(0.5 + 0.8 * i)
    return 'fail'


def main():
    todo = sorted(collect_samples(), key=priority)
    if os.path.exists(SAMPLE_LIST):
        os.remove(SAMPLE_LIST)
    with open(SAMPLE_LIST, 'w', encoding='utf-8') as f:
        json.dump(todo, f, ensure_ascii=False, indent=0)
    print(f'待下载 {len(todo)} 个采样', flush=True)

    t0 = time.time()
    ok = skip = fail = 0
    sess = session()
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(download, r, sess, 4, k % 2): r for k, r in enumerate(todo)}
        for k, fut in enumerate(as_completed(futs)):
            st = fut.result()
            ok += st == 'ok'
            skip += st == 'skip'
            fail += st == 'fail'
            if (k + 1) % 25 == 0:
                el = time.time() - t0
                print(f'  {k + 1}/{len(todo)} ok={ok} skip={skip} fail={fail} '
                      f'{el:.0f}s ({(k + 1) / el:.2f} files/s)', flush=True)

    print(f'第一轮: ok={ok} skip={skip} fail={fail} {time.time() - t0:.0f}s', flush=True)
    bad = [r for r in todo if not (os.path.exists(os.path.join(ROOT, r)) and
                                   os.path.getsize(os.path.join(ROOT, r)) > 1000)]
    for rnd in range(3):
        if not bad:
            break
        print(f'补漏第 {rnd + 1} 轮: {len(bad)} 个', flush=True)
        still = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(download, r, sess, 8, k % 3): r for k, r in enumerate(bad)}
            for fut in as_completed(futs):
                if fut.result() != 'ok':
                    still.append(futs[fut])
        bad = still
    print(f'完成: 剩余失败 {len(bad)}', flush=True)
    for r in bad[:20]:
        print('  FAIL', r, flush=True)


if __name__ == '__main__':
    main()
