"""셀 파일별 최적 팔레트: 인접 색인 쌍 빈도 × 팔레트 색차 합 최소."""
import sys, json, numpy as np
sys.path.insert(0, 'tools')
import romio, cel
r = romio.load(); nm = romio.names(r)
names = [n for n in nm if n and n.endswith('.pal')]
P = np.zeros((len(names), 256, 3), np.int32); L = np.zeros(len(names), np.int32)
for i, n in enumerate(names):
    p = romio.palette(romio.get(r, nm, n)); L[i] = len(p); P[i, :len(p)] = p
out = {}
for n in sorted(x for x in nm if x and x.endswith('.cel')):
    d = romio.get(r, nm, n); _, ims = cel.find_images(d)
    if not ims: continue
    M = np.zeros((256, 256), np.int64); mx = 0
    for s, x, y, w, h, px in ims:
        a = cel.untile(px, w, h).astype(np.int64)
        mx = max(mx, int(a.max()))
        for u, v in ((a[:, :-1], a[:, 1:]), (a[:-1], a[1:])):
            m = (u != 0) & (v != 0)  # 투명(0) 제외
            np.add.at(M, (u[m], v[m]), 1)
    ia, ib = np.nonzero(M); c = M[ia, ib]
    if len(c) == 0: continue
    cost = (np.abs(P[:, ia] - P[:, ib]).sum(-1) * c).sum(-1).astype(float)
    cost[L <= mx] = np.inf
    out[n.split('/')[-1][:-4]] = names[int(cost.argmin())] if np.isfinite(cost.min()) else None
json.dump(out, open('work/celpal.json', 'w'), indent=0)
print(len(out))
