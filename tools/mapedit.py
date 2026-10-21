"""배경 맵(.set+.map) 속 글자 교체.

맵을 색인 이미지로 펼쳐 수정한 뒤, 중복 타일을 합쳐 .set/.map을 다시 만든다.
글자 지우기: 영역 안 글자 픽셀(밝기 조건)과 그 주변을 마스크로 잡고 바깥 픽셀 색인으로 메운다.
"""
import struct
import numpy as np
import gfx, imgedit as ie


def load_index(r, nm, k):
    from palmatch import index_image
    return index_image(k)


def rebuild(r, nm, k, a):
    """색인 이미지 a로 .set/.map 재생성(타일 뒤집기 재사용 포함)."""
    old = romio_get(r, nm, f'res/art/{k}.map')
    hdr_a, w, h, hdr_b, _ = gfx.parse_map(old)
    assert a.shape == (h * 8, w * 8)
    tiles = []; index = {}; ent = []
    for ty in range(h):
        for tx in range(w):
            t = a[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            found = None
            for flag, v in ((0, t), (1, t[:, ::-1]), (2, t[::-1]), (3, t[::-1, ::-1])):
                key = v.tobytes()
                if key in index:
                    found = (index[key], flag); break
            if found is None:
                index[t.tobytes()] = len(tiles); tiles.append(t.tobytes()); found = (len(tiles) - 1, 0)
            i, flag = found
            ent.append(i | (flag & 1) << 10 | (flag >> 1) << 11)
    assert len(tiles) <= 1024, len(tiles)
    setd = struct.pack('<I', len(tiles)) + b''.join(tiles)
    mapd = struct.pack('<IHHI', hdr_a, w, h, hdr_b) + struct.pack(f'<{w*h}H', *ent)
    old_set = romio_get(r, nm, f'res/art/{k}.set')
    return setd + old_set[len(setd):] if False else setd, mapd + old[len(mapd):]


def romio_get(r, nm, n):
    import romio
    return romio.get(r, nm, n)


def inpaint(a, mask):
    """마스크 픽셀을 바깥 이웃 색인으로 채운다(바깥에서 안쪽으로 번져 들어감)."""
    a = a.copy(); m = mask.copy(); H, W = a.shape
    while m.any():
        prev = m.sum()
        for dy, dx in ((0, -1), (0, 1)) if m.sum() == prev and False else ((0, -1), (0, 1), (-1, 0), (1, 0)):
            src = np.zeros_like(m); val = np.zeros_like(a)
            ys = slice(max(dy, 0), H + min(dy, 0)); yd = slice(max(-dy, 0), H + min(-dy, 0))
            xs = slice(max(dx, 0), W + min(dx, 0)); xd = slice(max(-dx, 0), W + min(-dx, 0))
            src[yd, xd] = ~m[ys, xs]; val[yd, xd] = a[ys, xs]
            fill = m & src
            a[fill] = val[fill]; m = m & ~fill
        if m.sum() == prev:
            break
    return a


def dilate(m, n=1):
    for _ in range(n):
        m = m | ie.edges(m)
    return m


def nearest_index(P, rgb, used):
    used = np.array(sorted(used))
    d = ((P[used].astype(int) - np.array(rgb)) ** 2).sum(1)
    return int(used[d.argmin()])
