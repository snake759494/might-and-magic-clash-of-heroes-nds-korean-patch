"""res/art 그래픽: .set(u32 타일수 + 8x8 8bpp 타일), .map(u32 ?, u16 w, u16 h, u32 ?, u16[w*h]), .pal(u16 n + RGB555[n])."""
import struct
from PIL import Image
import romio


def tiles(raw):
    n = struct.unpack_from('<I', raw)[0]
    return [raw[4 + i * 64:4 + i * 64 + 64] for i in range(n)]


def parse_map(raw):
    a, w, h, b = struct.unpack_from('<IHHI', raw)
    return a, w, h, b, list(struct.unpack_from(f'<{w*h}H', raw, 12))


def render_map(r, nm, k, pal=None):
    T = tiles(romio.get(r, nm, f'res/art/{k}.set'))
    a, w, h, b, ent = parse_map(romio.get(r, nm, f'res/art/{k}.map'))
    pal = pal or romio.palette(romio.get(r, nm, f'res/art/{k}.pal'))
    img = Image.new('RGB', (w * 8, h * 8))
    px = img.load()
    for i, e in enumerate(ent):
        t = e & 0x3FF; hf = e >> 10 & 1; vf = e >> 11 & 1
        if t >= len(T):
            continue
        tx, ty = i % w * 8, i // w * 8
        for y in range(8):
            for x in range(8):
                v = T[t][y * 8 + x]
                if v < len(pal):
                    px[tx + (7 - x if hf else x), ty + (7 - y if vf else y)] = pal[v]
    return img
