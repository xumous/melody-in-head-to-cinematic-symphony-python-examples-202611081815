# -*- coding: utf-8 -*-
"""校验 MIDI：轨数、通道、音符事件数、时长（tick 覆盖范围）。"""
import struct
import sys

path = sys.argv[1] if len(sys.argv) > 1 else 'epic_final.mid'
data = open(path, 'rb').read()
assert data[:4] == b'MThd', 'not midi'
fmt, ntrk, tpq = struct.unpack('>HHH', data[8:14])
print(f'format={fmt} tracks={ntrk} TPQ={tpq} size={len(data)}')

pos = 8 + struct.unpack('>I', data[4:8])[0]

channels = {}
total_notes = 0
max_tick = 0
while pos < len(data):
    if data[pos:pos + 4] != b'MTrk':
        break
    ln = struct.unpack('>I', data[pos + 4:pos + 8])[0]
    body = data[pos + 8:pos + 8 + ln]
    i = 0
    tick = 0
    while i < len(body) and body[i] != 0xFF or i < 0:
        break
    # 简易解析：跳过 delta
    i = 0
    while i < len(body):
        # delta
        d = 0
        while body[i] & 0x80:
            d = (d << 7) | (body[i] & 0x7F)
            i += 1
        d = (d << 7) | body[i]
        i += 1
        tick += d
        max_tick = max(max_tick, tick)
        st = body[i]
        if st == 0xFF:
            meta = body[i + 1]
            i += 2
            l = 0
            while body[i] & 0x80:
                l = (l << 7) | (body[i] & 0x7F)
                i += 1
            l = (l << 7) | body[i]
            i += 1 + l
        elif st >> 4 == 0x9:
            ch = st & 0x0F
            channels[ch] = channels.get(ch, 0) + 1
            total_notes += 1
            i += 3
        elif st >> 4 == 0xB:
            i += 3
        else:
            i += 2
    pos += 8 + ln

print('note-on events per channel:', channels, 'total', total_notes)
print(f'last tick {max_tick} = {max_tick / tpq:.2f} beats = {max_tick / tpq * 0.3125:.2f} s')
