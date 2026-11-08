# -*- coding: utf-8 -*-
"""下载 Sonatina Symphonic Orchestra (SSO) —— 支持断点续传与重试。

本地 raw.githubusercontent.com / codeload.github.com 被限速，改走 gh-proxy 镜像。
"""
import os, time, zipfile, urllib.request, urllib.error

URL = 'https://gh-proxy.com/https://github.com/peastman/sso/archive/refs/heads/master.zip'
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'soundfonts')
ZIP_PATH = os.path.join(OUT_DIR, 'sso_master.zip')
os.makedirs(OUT_DIR, exist_ok=True)


def _download_once():
    have = os.path.getsize(ZIP_PATH) if os.path.exists(ZIP_PATH) else 0
    headers = {'User-Agent': 'Mozilla/5.0'}
    if have:
        headers['Range'] = f'bytes={have}-'
    req = urllib.request.Request(URL, headers=headers)
    try:
        r = urllib.request.urlopen(req, timeout=90)
    except urllib.error.HTTPError as e:
        if e.code == 416:  # 已经下完
            return have
        raise
    mode = 'ab' if have and r.status == 206 else 'wb'
    if mode == 'wb':
        have = 0
    t0 = time.time()
    written = have
    last_report = 0
    with r, open(ZIP_PATH, mode) as f:
        while True:
            chunk = r.read(512 * 1024)
            if not chunk:
                break
            f.write(chunk)
            written += len(chunk)
            if written - last_report > 25 * 1024 * 1024:
                el = time.time() - t0
                print(f'{written / 1e6:8.1f} MB  {written / 1e6 / el:5.2f} MB/s', flush=True)
                last_report = written
    return written


def download():
    for attempt in range(12):
        try:
            n = _download_once()
            print(f'attempt {attempt + 1}: size {n / 1e6:.1f} MB', flush=True)
        except Exception as e:
            print(f'attempt {attempt + 1} failed: {type(e).__name__} {e}', flush=True)
        if ok_zip():
            print('zip OK', flush=True)
            return
        time.sleep(2)
    raise RuntimeError('download failed after retries')


def ok_zip():
    if not os.path.exists(ZIP_PATH):
        return False
    try:
        with zipfile.ZipFile(ZIP_PATH) as z:
            bad = z.testzip()
            return bad is None and len(z.namelist()) > 100
    except Exception:
        return False


def unzip():
    with zipfile.ZipFile(ZIP_PATH) as z:
        z.extractall(OUT_DIR)
    print('extracted to', OUT_DIR)


if __name__ == '__main__':
    if ok_zip():
        print('already have valid zip')
    elif not os.path.exists(ZIP_PATH) or os.path.getsize(ZIP_PATH) < 1_000_000:
        download()
    else:
        download()
    if ok_zip():
        unzip()
    else:
        print('ZIP INVALID')
