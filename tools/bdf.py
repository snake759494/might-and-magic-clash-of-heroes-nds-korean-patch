"""BDF 비트맵 폰트 로더: {코드포인트: (dwidth, w, h, xoff, yoff, rows[bool])}."""


def load(path):
    glyphs = {}; cur = None; rows = None
    for line in open(path, encoding='latin-1'):
        p = line.split()
        if not p:
            continue
        if p[0] == 'STARTCHAR':
            cur = {}
        elif p[0] == 'ENCODING' and cur is not None:
            cur['c'] = int(p[1])
        elif p[0] == 'DWIDTH' and cur is not None:
            cur['dw'] = int(p[1])
        elif p[0] == 'BBX' and cur is not None:
            cur['bbx'] = tuple(map(int, p[1:5]))
        elif p[0] == 'BITMAP':
            rows = []
        elif p[0] == 'ENDCHAR':
            w, h, xo, yo = cur['bbx']
            bits = [[(int(r, 16) >> (len(r) * 4 - 1 - x)) & 1 for x in range(w)] for r in rows]
            glyphs[cur['c']] = (cur.get('dw', w), w, h, xo, yo, bits)
            cur = None; rows = None
        elif rows is not None:
            rows.append(p[0])
    return glyphs
