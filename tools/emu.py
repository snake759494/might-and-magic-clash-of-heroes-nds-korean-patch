"""헤드리스 DeSmuME 실행기. 사용: emu.py rom actions.json
actions: [{"keys":"a","hold":2,"wait":60,"shot":"name","touch":[x,y],"load":"st","save":"st","frames":n,"dump":"path"}]
창을 만들지 않고 내부 입력 API만 사용하며 끝나면 코어를 종료한다."""
import sys, json, os
from pathlib import Path
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask

rom = Path(sys.argv[1]).resolve(); acts = json.loads(Path(sys.argv[2]).read_text(encoding='utf8'))
out = Path('work/shots').resolve(); out.mkdir(parents=True, exist_ok=True)
st = Path('work/states').resolve(); st.mkdir(parents=True, exist_ok=True)
e = DeSmuME(); e.volume_set(0); e.open(str(rom))
try:
    for a in acts:
        if 'load' in a: e.savestate.load_file(str(st / a['load']))
        mask = 0
        for k in a.get('keys', '').split('+'):
            if k: mask |= keymask(getattr(Keys, 'KEY_' + k.upper()))
        if mask: e.input.keypad_add_key(mask)
        if 'touch' in a: e.input.touch_set_pos(*a['touch'])
        for _ in range(a.get('hold', 3 if mask or 'touch' in a else 0)): e.cycle(with_joystick=False)
        if mask: e.input.keypad_rm_key(mask)
        if 'touch' in a: e.input.touch_release()
        for _ in range(a.get('wait', 30)): e.cycle(with_joystick=False)
        if 'shot' in a: e.screenshot().save(out / (a['shot'] + '.png'))
        if 'save' in a: e.savestate.save_file(str(st / a['save']))
        if 'dump' in a:
            m = a['dump']; data = bytes(e.memory.unsigned[m['addr']:m['addr'] + m['len']])
            Path(m['path']).write_bytes(data)
finally:
    e.destroy()
print('done')
