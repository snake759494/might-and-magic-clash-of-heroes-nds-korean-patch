"""메인 RAM 덤프에서 게임 힙의 빈 블록 합계(KB)."""
import struct, sys
from pathlib import Path
a = (Path(__file__).resolve().parents[1] / 'work/arm9.bin').read_bytes()
TB = struct.unpack_from('<I', a, 0x2036CD4 - 0x2000000)[0]


def free_kb(ram):
    rd = lambda ad: struct.unpack_from('<I', ram, ad - 0x2000000)[0]
    p = rd(0x219B084); tot = 0; mx = 0; n = 0
    while 0x2000000 <= p < 0x2400000 and n < 5000:
        lo, hi = struct.unpack_from('<HH', ram, p - 0x2000000); size = rd(p + 4)
        tot += size; mx = max(mx, size); n += 1
        idx = hi & 0x3FFF
        p = 0 if idx == 0x3FFF else TB + idx * 8
    return tot // 1024, mx // 1024


if __name__ == '__main__':
    for f in sys.argv[1:]:
        print(f, free_kb(Path(f).read_bytes()))
