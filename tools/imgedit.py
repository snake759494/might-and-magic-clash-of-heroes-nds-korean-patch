"""셀·맵 이미지 속 영문을 한글로 다시 그리는 도구.

셀 이미지는 8x8 타일 순서 8bpp, 맵은 타일셋(.set)+타일맵(.map).
글자 색은 원본 이미지에서 행별 채움색/외곽색을 뽑아 그대로 쓴다.
"""
import collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cel as celmod
import hfont


def tile(a):
    h, w = a.shape
    return a.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).tobytes()


def text_mask(text, font, size, max_w, max_h, thresh=100, stroke=0):
    """텍스트를 이진 마스크로. 폭/높이에 맞을 때까지 크기를 줄인다."""
    while size > 5:
        f = ImageFont.truetype(str(font), size)
        l, t, r, b = f.getbbox(text, stroke_width=stroke)
        if r - l <= max_w and b - t <= max_h:
            break
        size -= 1
    img = Image.new('L', (r - l + 2, b - t + 2), 0)
    ImageDraw.Draw(img).text((-l + 1, -t + 1), text, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
    m = np.array(img) >= thresh
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def bdf_text_mask(text, name, gap=1):
    """갈무리 BDF로 한 줄 마스크(기준선 정렬, DWIDTH 진행폭 사용)."""
    hfont.bdf_mask(name, '가')  # 캐시 적재
    g = hfont._bdf_cache[name]
    asc = max(v[2] + v[4] for v in (g[ord(c)] for c in '가A') )
    desc = max(-v[4] for v in g.values() if v[4] < 0) if any(v[4] < 0 for v in g.values()) else 0
    H = asc + desc
    x = 0; cols = []
    for ch in text:
        dw, w, h, xo, yo, bits = g.get(ord(ch), g[ord('?')])
        cols.append((x + xo, asc - (h + yo), np.array(bits, bool).reshape(h, w) if h else np.zeros((0, 0), bool)))
        x += dw + (gap - 1 if not ch.isspace() else 0)
    W = max(x, max((cx + m.shape[1] for cx, cy, m in cols), default=1))
    out = np.zeros((H, W), bool)
    for cx, cy, m in cols:
        if m.size:
            out[cy:cy + m.shape[0], cx:cx + m.shape[1]] |= m
    ys, xs = np.nonzero(out)
    return out[ys.min():ys.max() + 1, :xs.max() + 1] if len(xs) else out


def edges(m):
    p = np.pad(m, 1)
    d = np.zeros_like(p)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            d |= np.roll(np.roll(p, dy, 0), dx, 1)
    return d[1:-1, 1:-1] & ~m


def row_colors(a, region, outline_set):
    """region(불리언) 안에서 행별 채움 색인 표."""
    fill = {}
    for y in range(a.shape[0]):
        c = collections.Counter(int(v) for v in a[y][region[y]] if v and int(v) not in outline_set)
        if c:
            fill[y] = c.most_common(1)[0][0]
    return fill


def draw_into(a, box, mask, fill_rows, outline_idx, outline=True, align='center', thick=1):
    """a: 색인 배열(수정됨), box=(x0,y0,x1,y1) 영역에 마스크를 그린다."""
    x0, y0, x1, y1 = box
    mh, mw = mask.shape
    ox = x0 + ((x1 - x0) - mw) // 2 if align == 'center' else x0
    oy = y0 + ((y1 - y0) - mh) // 2
    full = np.zeros(a.shape, bool)
    full[max(oy, 0):oy + mh, max(ox, 0):ox + mw] = mask[max(-oy, 0):, max(-ox, 0):][:a.shape[0] - max(oy, 0), :a.shape[1] - max(ox, 0)]
    if outline:
        e = full.copy()
        for _ in range(thick):
            e = e | edges(e)
        a[e & ~full] = outline_idx
    ys = sorted(fill_rows)
    for y, x in zip(*np.nonzero(full)):
        # 마스크 높이를 원본 글자 행 범위로 비례 대응
        r = (y - oy) / max(1, mh - 1)
        src = ys[min(len(ys) - 1, int(round(r * (len(ys) - 1))))] if ys else y
        a[y, x] = fill_rows.get(src, fill_rows[ys[0]] if ys else 1)
    return a


def parse_frames(d):
    import struct
    nf, npart = struct.unpack_from('<HH', d, 0)
    starts = list(struct.unpack_from(f'<{nf}H', d, 4))
    p = 4 + 2 * nf
    parts = [struct.unpack_from('<hhHH', d, p + i * 8) for i in range(npart)]
    frames = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < nf else npart
        frames.append(parts[s:e])
    return frames


def style_from(arrs):
    """원본 글자 이미지에서 (외곽선, 그림자, 행별 채움색, 글자 행 범위)를 얻는다."""
    edge = collections.Counter(); below = collections.Counter(); tot = collections.Counter()
    ys = set()
    for a in arrs:
        m = a > 0
        p = np.pad(m, 1)
        touch = ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]) & m
        for v in a[m].tolist(): tot[v] += 1
        for v in a[touch].tolist(): edge[v] += 1
        ys |= set(np.nonzero(m.any(1))[0].tolist())
    outl = edge.most_common(1)[0][0]
    # 그림자: 외곽선 색 픽셀의 바로 아래에 자주 오는 다른 가장자리 색
    for a in arrs:
        up = np.zeros_like(a); up[1:] = a[:-1]
        sel = (a > 0) & (a != outl) & (up == outl)
        for v in a[sel].tolist(): below[v] += 1
    shadow = None
    for v, c in below.most_common():
        if edge[v] / tot[v] > 0.5 and c > 10:
            shadow = v; break
    rows = collections.defaultdict(collections.Counter)
    for a in arrs:
        for y in range(a.shape[0]):
            for v in a[y].tolist():
                if v and v not in (outl, shadow): rows[y][v] += 1
    fill = {y: c.most_common(1)[0][0] for y, c in rows.items() if c}
    return outl, shadow, fill, (min(ys), max(ys))


def paint(canvas, oy, ox, mask, outl, shadow, fill, thick=1):
    """마스크를 (oy, ox)에 그린다: 그림자 → 외곽선 → 채움(행별 색 비례 대응)."""
    H, W = canvas.shape
    full = np.zeros((H, W), bool)
    mh, mw = mask.shape
    full[oy:oy + mh, ox:ox + mw] = mask[:H - oy, :W - ox]
    ol = full.copy()
    for _ in range(thick):
        ol = ol | edges(ol)
    if shadow is not None:
        sh = np.zeros_like(ol); sh[1:, 1:] = ol[:-1, :-1]
        canvas[sh & ~ol] = shadow
    canvas[ol & ~full] = outl
    fys = sorted(fill)
    for y, x in zip(*np.nonzero(full)):
        r = (y - oy) / max(1, mh - 1)
        canvas[y, x] = fill[fys[min(len(fys) - 1, int(round(r * (len(fys) - 1))))]]


def glyph_mask(text, spec, max_w, max_h):
    """spec: ('bdf', 이름) 또는 ('ttf', 경로, 크기)."""
    if spec[0] == 'bdf':
        m = bdf_text_mask(text, spec[1], gap=spec[2] if len(spec) > 2 else 1)
        if len(spec) > 3 and spec[3]:  # 가로 굵게
            b = m.copy(); b[:, 1:] |= m[:, :-1]
            m = np.concatenate([b, m[:, -1:] & False], 1)
            m[:, -1] = b[:, -1] & False
        return m
    # 글자 높이가 max_h가 되는 크기를 찾는다(한글 기준)
    size = 6
    for sz in range(6, 64):
        f = ImageFont.truetype(str(spec[1]), sz)
        l, t, r, b = f.getbbox('한글')
        if b - t <= max_h:
            size = sz
    return text_mask(text, spec[1], size, max_w, max_h, thresh=spec[2] if len(spec) > 2 else 110)


def retext_frame(d, frame, text, spec, imgs_override, thick=1, keep_other=False):
    _, ims = celmod.find_images(d)
    parts = parse_frames(d)[frame]
    arr = {i: imgs_override.get(i, celmod.untile(ims[i][5], ims[i][3], ims[i][4]).copy()) for _, _, i, _ in parts}
    x0 = min(x for x, y, i, f in parts); x1 = max(x + ims[i][3] for x, y, i, f in parts)
    y0 = min(y for x, y, i, f in parts); y1 = max(y + ims[i][4] for x, y, i, f in parts)
    canvas = np.zeros((y1 - y0, x1 - x0), np.uint8)
    for x, y, i, f in parts:
        h, w = arr[i].shape; canvas[y - y0:y - y0 + h, x - x0:x - x0 + w] = arr[i]
    outl, shadow, fill, (ta, tb) = style_from([canvas])
    if keep_other:
        # 외곽선 색이 있는 행 범위만 글자 영역으로 본다
        rows = np.nonzero((canvas == outl).sum(1) >= 2)[0]
        ta, tb = int(rows.min()), int(rows.max())
        textcols = {outl, shadow} | set(fill.values())
        base = canvas.copy()
        base[ta:tb + 1][np.isin(base[ta:tb + 1], list(c for c in textcols if c is not None))] = 0
        fill = {y: c for y, c in fill.items() if ta <= y <= tb}
    body_h = tb - ta + 1 - 2 * thick - (1 if shadow is not None else 0)
    m = glyph_mask(text, spec, canvas.shape[1] - 2 * thick - 2, body_h)
    new = base if keep_other else np.zeros_like(canvas)
    oy = ta + thick + max(0, (body_h - m.shape[0]) // 2)
    ox = max(thick, (canvas.shape[1] - m.shape[1]) // 2)
    paint(new, oy, ox, m, outl, shadow, {y - ta: c for y, c in fill.items()}, thick)
    out = {}
    for x, y, i, f in parts:
        h, w = arr[i].shape
        out[i] = new[y - y0:y - y0 + h, x - x0:x - x0 + w].copy()
    return out


def preview(arrs, path, scale=3):
    """역할별 가짜 색으로 미리보기(외곽선=검정, 그림자=회색, 채움=색인 해시)."""
    rows = []
    for a in arrs:
        img = np.zeros(a.shape + (3,), np.uint8); img[:] = (40, 40, 80)
        for v in np.unique(a):
            if v == 0: continue
            v = int(v); img[a == v] = ((v * 97) % 200 + 55, (v * 57) % 200 + 55, (v * 31) % 200 + 55)
        rows.append(Image.fromarray(img))
    W = max(r.width for r in rows); H = sum(r.height + 2 for r in rows)
    sh = Image.new('RGB', (W, H)); y = 0
    for r in rows: sh.paste(r, (0, y)); y += r.height + 2
    sh.resize((W * scale, H * scale), 0).save(path)


def write_images(d, newimgs):
    """셀 데이터 d의 이미지들을 교체(크기 동일)."""
    d = bytearray(d); _, ims = celmod.find_images(bytes(d))
    for i, a in newimgs.items():
        s, x, y, w, h, px = ims[i]
        assert a.shape == (h, w)
        d[s + 8:s + 8 + w * h] = tile(a.astype(np.uint8)) if w % 8 == 0 and h % 8 == 0 else a.astype(np.uint8).tobytes()
    return bytes(d)


def lines_mask(lines, spec, gap_y=1):
    ms = [glyph_mask(t, spec, 999, 99) for t in lines]
    W = max(m.shape[1] for m in ms); H = sum(m.shape[0] for m in ms) + gap_y * (len(ms) - 1)
    out = np.zeros((H, W), bool); y = 0
    for m in ms:
        x = (W - m.shape[1]) // 2; out[y:y + m.shape[0], x:x + m.shape[1]] = m; y += m.shape[0] + gap_y
    return out


def retext_region(a, box, lines, spec, bg=0, outline=None, fill=None, shadow=None, thick=1, gap_y=1):
    """a의 box=(x0,y0,x1,y1) 영역 글자를 지우고 다시 쓴다. bg: 배경 색인(0=투명).
    outline/fill/shadow를 주지 않으면 원본 글자에서 추출. outline=False면 외곽선 없음."""
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1].copy()
    txt = np.where(sub != bg, sub, 0).astype(np.uint8)
    o, s, f, _ = style_from([txt]) if txt.any() else (1, None, {0: 1}, (0, 0))
    if outline is None: outline = o
    if shadow is None: shadow = s if outline is not False else None
    if fill is None:
        fill = f
        if outline is False or not fill:
            vals = txt[txt > 0]
            fill = int(np.bincount(vals).argmax()) if len(vals) else 1
    if isinstance(fill, int): fill = {0: fill}
    m = lines_mask(lines, spec, gap_y)
    sub[:] = bg
    th = thick if outline is not False else 0
    H, W = sub.shape
    oy = max(th, (H - m.shape[0]) // 2); ox = max(th, (W - m.shape[1]) // 2)
    fr = {y - min(fill): c for y, c in fill.items()}
    if outline is False:
        full = np.zeros((H, W), bool); full[oy:oy + m.shape[0], ox:ox + m.shape[1]] = m[:H - oy, :W - ox]
        ys = sorted(fr)
        for yy, xx in zip(*np.nonzero(full)):
            r = (yy - oy) / max(1, m.shape[0] - 1); sub[yy, xx] = fr[ys[min(len(ys) - 1, int(round(r * (len(ys) - 1))))]]
    else:
        paint(sub, oy, ox, m, outline, shadow, fr, th)
    if m.shape[0] + 2 * th > H or m.shape[1] + 2 * th > W:
        print('  경고: 영역 초과', lines, m.shape, (H, W))
    a[y0:y1, x0:x1] = sub
    return a


def preview_pairs(arrs, path, scale=3, cols=4):
    """(원본, 수정) 쌍을 가로로 나란히, 여러 열로 배치."""
    def col(a):
        img = np.zeros(a.shape + (3,), np.uint8); img[:] = (40, 40, 80)
        for v in np.unique(a):
            v = int(v)
            if v: img[a == v] = ((v * 97) % 200 + 55, (v * 57) % 200 + 55, (v * 31) % 200 + 55)
        return Image.fromarray(img)
    pairs = [(col(arrs[i]), col(arrs[i + 1])) for i in range(0, len(arrs), 2)]
    cw = max(a.width + b.width + 6 for a, b in pairs); rh = max(a.height for a, b in pairs) + 4
    rows = (len(pairs) + cols - 1) // cols
    sh = Image.new('RGB', (cw * cols, rh * rows), (10, 10, 10))
    for n, (a, b) in enumerate(pairs):
        x, y = n % cols * cw, n // cols * rh
        sh.paste(a, (x, y)); sh.paste(b, (x + a.width + 3, y))
    sh.resize((sh.width * scale, sh.height * scale), 0).save(path)
