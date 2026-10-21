"""원본 폰트의 색인 스타일(행별 채움색·외곽선색)을 분석해 한글 마스크를 같은 스타일로 칠한다."""
import collections
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import bdf

ROOT = Path(__file__).resolve().parents[1]
GALMURI = ROOT / 'work/fonts/galmuri'
_bdf_cache = {}


def nb4(px, w, h, x, y):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        xx, yy = x + dx, y + dy
        if not (0 <= xx < w and 0 <= yy < h) or not px[yy * w + xx]:
            return True
    return False


class Style:
    """원본 대문자·소문자 글리프에서 기준선 상대 행(y)별 채움/외곽선 색인을 수집."""

    def __init__(self, font):
        self.font = font
        fill = collections.defaultdict(collections.Counter)
        edge = collections.defaultdict(collections.Counter)
        edge_ratio = collections.Counter(); total = collections.Counter()
        letters = [c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefhiklmnorstuvwxz0123456789']
        for ch in letters:
            i = ord(ch) - 0x21
            if i >= len(font.glyphs) or not font.glyphs[i][4]:
                continue
            w, h, gx, gy, px = font.glyphs[i]
            for y in range(h):
                for x in range(w):
                    v = px[y * w + x]
                    if not v:
                        continue
                    total[v] += 1
                    if nb4(px, w, h, x, y):
                        edge_ratio[v] += 1; edge[gy + y][v] += 1
                    else:
                        fill[gy + y][v] += 1
        # 투명 영역(또는 글리프 경계)에 자주 닿는 색인 = 외곽선 색
        self.outline_idx = {v for v in total if edge_ratio[v] / total[v] > 0.25 and total[v] > 20}
        edge_total = sum(sum(c.values()) for c in edge.values())
        edge_outline = sum(c[v] for c in edge.values() for v in self.outline_idx)
        self.outlined = bool(edge_total and edge_outline / edge_total > 0.6)
        if self.outlined:
            for y in set(fill):
                for v in self.outline_idx:
                    if fill[y][v]:
                        edge[y][v] += fill[y][v]; del fill[y][v]
        self.fill = {}; self.edge = {}
        for y in set(fill) | set(edge):
            f = collections.Counter({k: v for k, v in (fill[y] + (edge[y] if not self.outlined else collections.Counter())).items() if not self.outlined or k not in self.outline_idx})
            if not f:
                f = fill[y] + edge[y]
            self.fill[y] = f.most_common(1)[0][0]
            e = collections.Counter({k: v for k, v in edge[y].items() if k in self.outline_idx}) or edge[y]
            if e:
                self.edge[y] = e.most_common(1)[0][0]
        caps = [font.glyphs[ord(c) - 0x21] for c in 'ABDEHKMNRTX' if font.glyphs[ord(c) - 0x21][4]]
        self.cap_top = collections.Counter(g[3] for g in caps).most_common(1)[0][0]
        self.cap_h = collections.Counter(g[1] for g in caps).most_common(1)[0][0]
        allg = [g for g in font.glyphs if g[4]]
        self.center = sorted(g[2] + g[0] / 2 for g in allg)[len(allg) // 2]

    def color(self, y, outline):
        table = self.edge if outline else self.fill
        if y in table:
            return table[y]
        ys = sorted(table)
        return table[min(ys, key=lambda k: abs(k - y))]

    def body_row(self, r, h):
        """한글 본체 r행(0..h-1)을 영문 대문자 본체 행으로 비례 대응."""
        o = 1 if self.outlined else 0
        a = self.cap_top + o; b = self.cap_top + self.cap_h - 1 - o
        return a + round(r * (b - a) / max(1, h - 1))

    def glyph(self, mask, top, add_outline):
        """mask: 2D bool 리스트(높이 x 폭), top: 기준선 상대 위쪽 y. 테두리 1px 추가 여부."""
        h = len(mask); w = len(mask[0]) if h else 0
        if add_outline:
            W, H = w + 2, h + 2
            m = [[False] * W for _ in range(H)]
            for y in range(h):
                for x in range(w):
                    m[y + 1][x + 1] = bool(mask[y][x])
            px = bytearray(W * H)
            for y in range(H):
                for x in range(W):
                    if m[y][x]:
                        px[y * W + x] = self.color(self.body_row(min(max(y - 1, 0), h - 1), h), False)
                    elif any(0 <= y + dy < H and 0 <= x + dx < W and m[y + dy][x + dx]
                             for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                        px[y * W + x] = self.color(self.body_row(min(max(y - 1, 0), h - 1), h), True)
            gtop = top - 1
        else:
            W, H = w, h
            px = bytearray(W * H)
            for y in range(H):
                for x in range(W):
                    if mask[y][x]:
                        px[y * W + x] = self.color(self.body_row(y, h), False)
            gtop = top
        gx = round(self.center - W / 2)
        return [W, H, gx, gtop, bytes(px)]


def bdf_mask(name, ch):
    if name not in _bdf_cache:
        _bdf_cache[name] = bdf.load(GALMURI / f'{name}.bdf')
    dw, w, h, xo, yo, bits = _bdf_cache[name][ord(ch)]
    return [[bool(b) for b in row] for row in bits], dw


def ttf_mask(path, size, ch, thresh=110, bold=0):
    f = ImageFont.truetype(str(path), size)
    l, t, r, b = f.getbbox('가')
    img = Image.new('L', (size * 2, size * 2), 0)
    d = ImageDraw.Draw(img)
    d.text((size // 2, size // 2), ch, font=f, fill=255, stroke_width=bold, stroke_fill=255)
    # 한글 공통 세로 범위(가 기준 상단~하단)로 자르고 가로는 실제 잉크 범위로 자른다.
    y0 = size // 2 + t; y1 = size // 2 + b
    px = img.load()
    cols = [x for x in range(img.width) if any(px[x, y] >= thresh for y in range(y0, y1))]
    if not cols:
        return [[False]], 1
    x0, x1 = cols[0], cols[-1] + 1
    return [[px[x, y] >= thresh for x in range(x0, x1)] for y in range(y0, y1)], x1 - x0
