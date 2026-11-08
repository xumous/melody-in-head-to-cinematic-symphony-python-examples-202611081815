# -*- coding: utf-8 -*-
"""探测可用的 GitHub 加速代理（国内带宽测试）。"""
import time, urllib.request, threading

RAW = ('Sonatina%20Symphonic%20Orchestra/Samples-looped/Cello/cello-a4.flac')
CANDIDATES = [
    'https://ghfast.top/https://raw.githubusercontent.com/peastman/sso/master/',
    'https://gh-proxy.com/https://raw.githubusercontent.com/peastman/sso/master/',
    'https://github.moeyy.xyz/https://raw.githubusercontent.com/peastman/sso/master/',
    'https://raw.gitmirror.com/peastman/sso/master/',
    'https://raw.kgithub.com/peastman/sso/master/',
    'https://ghproxy.net/https://raw.githubusercontent.com/peastman/sso/master/',
]
results = {}


def probe(base):
    url = base + RAW
    t0 = time.time()
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15)
        total = 0
        while time.time() - t0 < 12:
            chunk = r.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
        el = time.time() - t0
        results[base] = (total, el, total / 1024 / el)
    except Exception as e:
        results[base] = (0, time.time() - t0, 0)


ths = [threading.Thread(target=probe, args=(b,)) for b in CANDIDATES]
[t.start() for t in ths]
[t.join() for t in ths]
for b in CANDIDATES:
    tot, el, sp = results[b]
    print(f'{sp:8.1f} kB/s  {tot / 1024:8.1f} kB/{el:5.1f}s  {b}')
