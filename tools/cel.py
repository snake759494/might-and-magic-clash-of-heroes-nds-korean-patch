"""res/art/*.cel: 프레임·파츠 정의 뒤에 8bpp 비트맵 묶음.
비트맵 묶음: u32 개수, u16 시작오프셋[개수-1](4바이트 단위), 4정렬, u32 총바이트,
각 이미지: s16 x, s16 y, u16 w, u16 h, w*h 픽셀."""
import struct


def find_images(d):
    """비트맵 묶음 위치를 앞에서부터 검증하며 찾는다."""
    for p in range(0, len(d) - 8, 2):
        n = struct.unpack_from('<I', d, p)[0]
        if not 1 <= n <= 4096:
            continue
        q0 = p + 4 + 2 * (n - 1)
        for q in (q0, q0 + (-q0) % 4):
            if q + 4 <= len(d) and q + 4 + struct.unpack_from('<I', d, q)[0] == len(d):
                break
        else:
            continue
        offs = [0] + list(struct.unpack_from(f'<{n-1}H', d, p + 4)) if n > 1 else [0]
        total = struct.unpack_from('<I', d, q)[0]
        base = q + 4
        if base + total != len(d):
            continue
        imgs = []; ok = True
        for i, o in enumerate(offs):
            s = base + o * 4
            if s + 8 > len(d): ok = False; break
            x, y, w, h = struct.unpack_from('<hhHH', d, s)
            if not (0 < w <= 256 and 0 < h <= 256) or s + 8 + w * h > len(d): ok = False; break
            imgs.append((s, x, y, w, h, d[s + 8:s + 8 + w * h]))
        if ok:
            return p, imgs
    return None, []


def untile(px, w, h):
    """8x8 타일 순서 픽셀을 선형(행 우선) 배열로."""
    import numpy as np
    a = np.frombuffer(px, np.uint8)
    if w % 8 or h % 8:
        return a.reshape(h, w)
    t = a.reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3)
    return t.reshape(h, w)
