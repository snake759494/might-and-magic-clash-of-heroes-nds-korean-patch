"""LZ11 압축 해제/압축 (NDS BIOS 호환)."""

def decompress(data):
    assert data[0] == 0x11
    size = int.from_bytes(data[1:4], 'little'); pos = 4
    if size == 0:
        size = int.from_bytes(data[4:8], 'little'); pos = 8
    out = bytearray()
    while len(out) < size:
        flags = data[pos]; pos += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if not flags & (0x80 >> bit):
                out.append(data[pos]); pos += 1
                continue
            b = data[pos]; ind = b >> 4
            if ind == 0:
                n = (((b & 0xF) << 4) | (data[pos + 1] >> 4)) + 0x11
                disp = ((data[pos + 1] & 0xF) << 8 | data[pos + 2]) + 1; pos += 3
            elif ind == 1:
                n = (((b & 0xF) << 12) | (data[pos + 1] << 4) | (data[pos + 2] >> 4)) + 0x111
                disp = ((data[pos + 2] & 0xF) << 8 | data[pos + 3]) + 1; pos += 4
            else:
                n = ind + 1
                disp = ((b & 0xF) << 8 | data[pos + 1]) + 1; pos += 2
            for _ in range(n):
                out.append(out[-disp])
    return bytes(out[:size])


def compress(data):
    data = bytes(data); n = len(data)
    out = bytearray([0x11]) + n.to_bytes(3, 'little')
    if n >= 1 << 24:
        out = bytearray([0x11, 0, 0, 0]) + n.to_bytes(4, 'little')
    # 해시 체인으로 일치 탐색
    head = {}; prev = [-1] * n
    def insert(i):
        if i + 3 <= n:
            k = data[i:i + 3]; prev[i] = head.get(k, -1); head[k] = i
    i = 0
    while i < n:
        flagpos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= n:
                break
            best = 0; bestd = 0
            if i + 3 <= n:
                j = head.get(data[i:i + 3], -1); tries = 0
                maxlen = min(0x10110, n - i)
                while j >= 0 and i - j <= 0x1000 and tries < 128:
                    l = 0
                    while l < maxlen and data[j + l] == data[i + l]:
                        l += 1
                    if l > best:
                        best, bestd = l, i - j
                        if l == maxlen:
                            break
                    j = prev[j]; tries += 1
            if best >= 3:
                d = bestd - 1
                if best <= 0x10:
                    out += bytes([((best - 1) << 4) | (d >> 8), d & 0xFF])
                elif best <= 0x110:
                    m = best - 0x11
                    out += bytes([m >> 4, ((m & 0xF) << 4) | (d >> 8), d & 0xFF])
                else:
                    m = best - 0x111
                    out += bytes([0x10 | (m >> 12), (m >> 4) & 0xFF, ((m & 0xF) << 4) | (d >> 8), d & 0xFF])
                flags |= 0x80 >> bit
                for k in range(best):
                    insert(i + k)
                i += best
            else:
                out.append(data[i]); insert(i); i += 1
        out[flagpos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)
