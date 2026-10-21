"""맵별 최적 팔레트: 인접 색인 쌍 빈도 × 팔레트 색차 합 최소."""
import sys, json, numpy as np
sys.path.insert(0, 'tools')
import romio, gfx
r = romio.load(); nm = romio.names(r)
names = [n for n in nm if n and n.endswith('.pal')]
P = np.zeros((len(names), 256, 3), np.int32); L = np.zeros(len(names), np.int32)
for i, n in enumerate(names):
    p = romio.palette(romio.get(r, nm, n)); L[i] = len(p); P[i, :len(p)] = p


def index_image(k):
    T = gfx.tiles(romio.get(r, nm, f'res/art/{k}.set'))
    a, w, h, b, ent = gfx.parse_map(romio.get(r, nm, f'res/art/{k}.map'))
    img = np.zeros((h * 8, w * 8), dtype=np.uint8)
    for i, e in enumerate(ent):
        t = e & 0x3FF
        if t >= len(T): continue
        tl = np.frombuffer(T[t], dtype=np.uint8).reshape(8, 8)
        if e >> 10 & 1: tl = tl[:, ::-1]
        if e >> 11 & 1: tl = tl[::-1]
        img[i // w * 8:i // w * 8 + 8, i % w * 8:i % w * 8 + 8] = tl
    return img


if __name__ == '__main__':
    out = {}
    for n in sorted(x for x in nm if x and x.endswith('.map')):
        k = n.split('/')[-1][:-4]
        a = index_image(k).astype(np.int64); mx = int(a.max())
        M = np.zeros((256, 256), np.int64)
        for u, v in ((a[:, :-1], a[:, 1:]), (a[:-1], a[1:])):
            np.add.at(M, (u.ravel(), v.ravel()), 1)
        ia, ib = np.nonzero(M); c = M[ia, ib]
        cost = (np.abs(P[:, ia] - P[:, ib]).sum(-1) * c).sum(-1).astype(float)
        cost[L <= mx] = np.inf
        out[k] = names[int(cost.argmin())]
    json.dump(out, open('work/palmatch.json', 'w'), indent=0)
    print(len(out))
