import sys, struct
from pathlib import Path
import ndspy.rom
sys.path.insert(0, str(Path(__file__).parent))
import lz11

ROOT = Path(__file__).resolve().parents[1]
_ROMNAME = 'Might & Magic - Clash of Heroes (USA) (En,Fr,Es).nds'
ORIG = ROOT / _ROMNAME if (ROOT / _ROMNAME).exists() else ROOT.parent / _ROMNAME


def load(path=ORIG):
    return ndspy.rom.NintendoDSRom.fromFile(str(path))


def names(r):
    return {r.filenames.filenameOf(i): i for i in range(len(r.files))}


def get(r, nm, name):
    d = r.files[nm[name]]
    return lz11.decompress(d) if d[:1] == b'\x11' else bytes(d)


def palette(raw):
    n = struct.unpack_from('<H', raw)[0]
    return [((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31) for c in struct.unpack_from(f'<{n}H', raw, 2)]
