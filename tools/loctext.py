"""로케일(.en) 파일: u32 풀 문자 수, u32 항목 수, u16 오프셋[항목], UTF-16 문자열 풀."""
import struct


def parse(d):
    tot, cnt = struct.unpack_from('<II', d)
    offs = struct.unpack_from(f'<{cnt}H', d, 8); base = 8 + 2 * cnt
    out = []
    for o in offs:
        p = base + o * 2; e = p
        while d[e:e + 2] != b'\0\0':
            e += 2
        out.append(d[p:e].decode('utf-16-le'))
    return out


def offsets(d):
    cnt = struct.unpack_from('<I', d, 4)[0]
    return list(struct.unpack_from(f'<{cnt}H', d, 8))


def build(strings, orig_offsets=None):
    """원본처럼 항목마다 따로 저장한다. orig_offsets가 있으면 원본에서 같은 오프셋을
    공유하던 항목(끝의 0 오프셋 센티널 등)만 공유를 유지한다."""
    pool = bytearray(); offs = []; seen = {}
    for i, s in enumerate(strings):
        key = orig_offsets[i] if orig_offsets else i
        if key not in seen:
            seen[key] = len(pool) // 2; pool += s.encode('utf-16-le') + b'\0\0'
        offs.append(seen[key])
    while len(pool) % 4:
        pool += b'\0\0'
    assert len(pool) // 2 < 0x10000
    head = struct.pack('<II', len(pool) // 2, len(strings)) + struct.pack(f'<{len(strings)}H', *offs)
    if len(head) % 4:
        head += b'\0\0'
    return head + bytes(pool)
