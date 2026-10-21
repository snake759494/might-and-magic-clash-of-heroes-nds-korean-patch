"""Clash of Heroes .font 형식.

u16 줄높이, u16 공백폭, s16 자간, u16 범위수,
범위마다 u16 상위바이트, u16 개수, 글리프[개수] (u8 폭, u8 높이, s8 x, s8 y, u32 픽셀오프셋|-1),
u32 픽셀크기, 8bpp 픽셀(같은 번호 .pal 색인).
조회: 상위바이트가 같은 범위를 찾고 하위바이트를 색인으로 쓴다. 상위바이트 0이면 0x21을 뺀다.
진행폭 = 글리프 폭 + 자간.
"""
import struct


class Font:
    def __init__(self, data):
        self.line, self.space, self.spacing, nr = struct.unpack_from('<HHhH', data, 0)
        p = 8; self.ranges = {}
        for _ in range(nr):
            hi, n = struct.unpack_from('<HH', data, p); p += 4
            ents = [struct.unpack_from('<BBbbI', data, p + i * 8) for i in range(n)]; p += n * 8
            self.ranges[hi] = ents
        size = struct.unpack_from('<I', data, p)[0]; base = p + 4
        for hi, ents in self.ranges.items():
            self.ranges[hi] = [[w, h, x, y, None if o == 0xFFFFFFFF else bytes(data[base + o:base + o + w * h])]
                               for w, h, x, y, o in ents]

    @property
    def glyphs(self):
        return self.ranges[0]

    def build(self, dedupe=True):
        head = bytearray(struct.pack('<HHhH', self.line, self.space, self.spacing, len(self.ranges)))
        pix = bytearray(); cache = {}
        for hi in sorted(self.ranges):
            ents = self.ranges[hi]
            head += struct.pack('<HH', hi, len(ents))
            for w, h, x, y, px in ents:
                if px is None:
                    head += struct.pack('<BBbbI', w, h, x, y, 0xFFFFFFFF)
                else:
                    key = (w, h, px)
                    if key not in cache or not dedupe:
                        cache[key] = len(pix); pix += px
                    head += struct.pack('<BBbbI', w, h, x, y, cache[key])
        while len(pix) % 4:
            pix.append(0)
        return bytes(head + struct.pack('<I', len(pix)) + pix)
