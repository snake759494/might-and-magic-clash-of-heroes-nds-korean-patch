"""폰트 파서의 할당 결과(0이면 실패)와 로드된 리소스를 기록하는 헤드리스 검사기.
사용: memprobe.py rom actions.json [shot접두어]"""
import sys, json
from pathlib import Path
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
e = DeSmuME(); e.volume_set(0); e.open(sys.argv[1])
pre = sys.argv[3] if len(sys.argv) > 3 else 'm'
out = Path('work/shots'); out.mkdir(parents=True, exist_ok=True)
fails = []; loads = []; frame = [0]
def rd(a, n): return bytes(e.memory.unsigned[a:a + n])
def cstr(a): return rd(a, 64).split(b'\0')[0].decode('latin-1')
def on_load(addr, size):
    r5 = e.memory.register_arm9.r0
    rid = int.from_bytes(rd(r5, 4), 'little')
    p = int.from_bytes(rd(0x20DB618 + rid * 4, 4), 'little')
    loads.append(cstr(p))
def chk(addr, size):
    if e.memory.register_arm9.r0 == 0:
        fails.append((frame[0], hex(addr), loads[-1] if loads else '?'))
e.memory.register_exec(0x2085804, on_load)
objname = {}; usage = {}
def on_parse(addr, size):
    objname[e.memory.register_arm9.r0] = loads[-1] if loads else '?'
def on_glyph(addr, size):
    r = e.memory.register_arm9
    n = objname.get(r.r0, hex(r.r0)); usage.setdefault(n, set()).add(r.r1 & 0xFFFF)
strs = {}
def on_measure(addr, size):
    r = e.memory.register_arm9
    fobj = int.from_bytes(rd(r.r0 + 0xC, 4), 'little'); n = objname.get(fobj, hex(fobj))
    ln = r.r3
    if 0 < ln < 400:
        t = rd(r.r1 + r.r2 * 2, ln * 2).decode('utf-16-le', 'replace')
        strs.setdefault(n, set()).add(t)
e.memory.register_exec(0x202A430, on_measure)
e.memory.register_exec(0x202A648, on_parse)
e.memory.register_exec(0x202A874, on_glyph)
for a in (0x202A6B0, 0x202A710, 0x202A768):
    e.memory.register_exec(a, chk)
def run(n):
    for _ in range(n):
        e.cycle(with_joystick=False); frame[0] += 1
for i, a in enumerate(json.load(open(sys.argv[2]))):
    if 'load' in a: e.savestate.load_file(str(Path('work/states') / a['load']))
    mask = 0
    for k in a.get('keys', '').split('+'):
        if k: mask |= keymask(getattr(Keys, 'KEY_' + k.upper()))
    if mask: e.input.keypad_add_key(mask)
    if 'touch' in a: e.input.touch_set_pos(*a['touch'])
    run(a.get('hold', 3 if mask or 'touch' in a else 0))
    if mask: e.input.keypad_rm_key(mask)
    if 'touch' in a: e.input.touch_release()
    run(a.get('wait', 30))
    if 'shot' in a: e.screenshot().save(out / f"{pre}{a['shot']}.png")
    if 'save' in a: e.savestate.save_file(str(Path('work/states') / a['save']))
# 이름 모르는 폰트 객체는 'A'와 'g' 글리프 픽셀로 원본 파일과 대조해 식별
sys.path.insert(0, 'tools')
import romio, fontlib
_r = romio.load(); _nm = romio.names(_r); sig = {}
for k in range(23):
    f = fontlib.Font(romio.get(_r, _nm, f'res/art/{k}.font'))
    sig.setdefault(tuple(g[4] for g in f.glyphs[0x20:0x48] if g), f'{k}.font')
def ident(obj):
    try:
        rp = int.from_bytes(rd(obj + 8, 4), 'little'); tp = int.from_bytes(rd(rp + 4, 4), 'little')
        n = int.from_bytes(rd(rp + 2, 2), 'little'); out = []
        for i in range(0x20, min(0x48, n)):
            w, h = rd(tp + i * 8, 2); pp = int.from_bytes(rd(tp + i * 8 + 4, 4), 'little')
            out.append(rd(pp, w * h) if pp else None)
        return sig.get(tuple(out), hex(obj))
    except Exception:
        return hex(obj)
for d in (usage, strs):
    for k in list(d):
        if k.startswith('0x'):
            nk = ident(int(k, 16)); d.setdefault(nk, set()).update(d.pop(k)) if nk != k else None
e.destroy()
print('FAILS', len(fails), fails[:10])
cm = json.loads(Path('work/charmap.json').read_text(encoding='utf8')) if Path('work/charmap.json').exists() else {}
rev = {int(v, 16): k for k, v in cm.items()}
Path('work/usage_' + pre + '.json').write_text(json.dumps({k: ''.join(rev.get(c, chr(c)) for c in sorted(v)) for k, v in usage.items()}, ensure_ascii=False, indent=1), encoding='utf8')
prev = {}
sp = Path('work/strings_' + pre + '.json')
if sp.exists(): prev = json.loads(sp.read_text(encoding='utf8'))
for k, v in strs.items(): prev[k] = sorted(set(prev.get(k, [])) | v)
sp.write_text(json.dumps(prev, ensure_ascii=False, indent=1), encoding='utf8')
print('USAGE', {k: len(v) for k, v in usage.items()})
print('FONTS', [x for x in loads if x.endswith('.font')][-30:])
