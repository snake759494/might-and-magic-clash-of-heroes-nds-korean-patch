"""원본 ROM의 영어 로케일(.en)에서 번역 대상 원문 목록 translation/src/*.json 을 만든다.
원문은 저장소에 포함하지 않으므로 빌드 전에 한 번 실행한다."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import romio, loctext

r = romio.load(); nm = romio.names(r)
out = romio.ROOT / 'translation/src'; out.mkdir(parents=True, exist_ok=True)
n = 0
for name in nm:
    if name and name.startswith('res/locales/') and name.endswith('.en'):
        k = name.split('/')[-1][:-3]
        s = loctext.parse(romio.get(r, nm, name))
        (out / f'{k}.json').write_text(json.dumps({str(i): x for i, x in enumerate(s)}, ensure_ascii=False, indent=1), encoding='utf8')
        n += 1
print('원문 파일', n)
