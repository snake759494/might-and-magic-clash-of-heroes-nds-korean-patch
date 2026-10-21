"""미국 국기 이미지를 같은 자리·같은 색조의 태극기로 바꾼다."""
import math
import numpy as np
from PIL import Image, ImageDraw


def taegeuk(W, H, ss=8):
    """W×H 태극기를 색 번호 배열(0=흰,1=빨강,2=파랑,3=검정)로. ss배 확대해 그린 뒤 다수결로 축소."""
    w, h = W * ss, H * ss
    img = Image.new('L', (w, h), 0); d = ImageDraw.Draw(img)
    cx, cy = w / 2, h / 2; R = h / 4
    # 태극: 위 빨강, 아래 파랑, 좌측 빨강 작은 원, 우측 파랑 작은 원(기울기 생략한 단순화)
    ang = math.atan2(2, 3)  # 대각선 기울기
    def rot(x, y, a):
        return cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)
    a0 = ang
    d.pieslice([cx - R, cy - R, cx + R, cy + R], math.degrees(a0) + 180, math.degrees(a0) + 360, fill=1)
    d.pieslice([cx - R, cy - R, cx + R, cy + R], math.degrees(a0), math.degrees(a0) + 180, fill=2)
    r2 = R / 2
    lx, ly = rot(-r2, 0, a0); rx, ry = rot(r2, 0, a0)
    d.ellipse([lx - r2, ly - r2, lx + r2, ly + r2], fill=1)
    d.ellipse([rx - r2, ry - r2, rx + r2, ry + r2], fill=2)
    # 4괘: (대각 방향 각도, 줄 모양 위→아래 True=끊김)
    bar_len = R * 0.9; bar_th = h / 18; gap = h / 20; dist = R * 1.25
    gwes = [(math.pi + ang, (False, False, False)),    # 건(좌상)
            (-ang, (True, False, True)),                 # 감(우상)
            (math.pi - ang, (False, True, False)),       # 리(좌하)
            (ang, (True, True, True))]                   # 곤(우하)
    for dirang, pattern in gwes:
        ux, uy = math.cos(dirang), math.sin(dirang)  # 중심→괘 방향
        vx, vy = -uy, ux                              # 막대 길이 방향
        for k, broken in enumerate(pattern):
            off = dist + k * (bar_th + gap) + bar_th / 2
            px, py = cx + ux * off, cy + uy * off
            segs = [(-bar_len / 2, -gap / 2), (gap / 2, bar_len / 2)] if broken else [(-bar_len / 2, bar_len / 2)]
            for s0, s1 in segs:
                pts = []
                for sl, t in ((s0, -bar_th / 2), (s1, -bar_th / 2), (s1, bar_th / 2), (s0, bar_th / 2)):
                    pts.append((px + vx * sl + ux * t, py + vy * sl + uy * t))
                d.polygon(pts, fill=3)
    a = np.array(img).reshape(H, ss, W, ss).transpose(0, 2, 1, 3).reshape(H, W, ss * ss)
    out = np.zeros((H, W), np.uint8)
    for y in range(H):
        for x in range(W):
            c = np.bincount(a[y, x], minlength=4)
            # 작은 그림이므로 검정/빨강/파랑이 1/4 이상이면 우선
            nz = c[1:].argmax() + 1
            out[y, x] = nz if c[nz] >= ss * ss * 0.45 else 0
    return out


def replace_us_flag(a, P):
    """a: 색인 배열(수정본 반환), P: 팔레트 RGB 배열(256,3)."""
    rgb = P[a].astype(int)
    red = (rgb[..., 0] > rgb[..., 1] + 40) & (rgb[..., 0] > rgb[..., 2] + 40) & (a > 0)
    blue = (rgb[..., 2] > rgb[..., 0] + 30) & (a > 0)
    m = red | blue
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sub = a[y0:y1, x0:x1]; srgb = rgb[y0:y1, x0:x1]
    ir = int(np.bincount(sub[red[y0:y1, x0:x1]]).argmax())
    ib = int(np.bincount(sub[blue[y0:y1, x0:x1]]).argmax())
    lum = srgb.sum(-1)
    white_mask = ~(red | blue)[y0:y1, x0:x1] & (sub > 0)
    iw = int(np.bincount(sub[white_mask & (lum >= np.percentile(lum[white_mask], 70))]).argmax())
    # 검정: 흰색 밝기에 비례한 어두운 색(팔레트 전체에서 가장 가까운 색)
    used = [i for i in range(1, 256)]
    k = P[iw].astype(int).sum() / (3 * 255)
    target = np.array([20, 20, 20]) * k
    ik = int(min(used, key=lambda i: ((P[i].astype(int) - target) ** 2).sum()))
    t = taegeuk(x1 - x0, y1 - y0)
    out = a.copy()
    out[y0:y1, x0:x1] = np.choose(t, [iw, ir, ib, ik]).astype(np.uint8)
    return out
