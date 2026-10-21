"""폰트별 한글 글리프 원천 설정. kind: bdf(갈무리) 또는 ttf(작업 폴더 글꼴)."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
_find = lambda n: ROOT / n if (ROOT / n).exists() else ROOT.parent / n
NEO = lambda w: _find(f'NanumSquareNeo-{w}.ttf')
HANGANG = lambda w: _find(f'SeoulHangang{w}.ttf')

# body_h: 한글 본체 높이(px), outline: 1px 테두리 추가 여부
CFG = {
    0: dict(kind='bdf', name='Galmuri9', outline=False),
    6: dict(kind='bdf', name='Galmuri9', outline=True),
    7: dict(kind='bdf', name='Galmuri9', outline=True),
    13: dict(kind='bdf', name='Galmuri9', outline=True),
    1: dict(kind='bdf', name='Galmuri7', outline=False),
    2: dict(kind='bdf', name='Galmuri9', outline=False),
    3: dict(kind='bdf', name='Galmuri9', outline=False),
    4: dict(kind='bdf', name='Galmuri9', outline=True),
    5: dict(kind='bdf', name='Galmuri9', outline=True),
    8: dict(kind='bdf', name='Galmuri7', outline=True),
    9: dict(kind='bdf', name='Galmuri7', outline=True),
    14: dict(kind='bdf', name='Galmuri9', outline=True),
    15: dict(kind='bdf', name='Galmuri9', outline=True),
    16: dict(kind='bdf', name='Galmuri9', outline=True),
    17: dict(kind='ttf', path=NEO('dEb'), body_h=15, outline=True),
    18: dict(kind='ttf', path=NEO('dEb'), body_h=15, outline=True),
    19: dict(kind='ttf', path=NEO('cBd'), body_h=13, outline=True),
    20: dict(kind='ttf', path=NEO('cBd'), body_h=13, outline=True),
    22: dict(kind='ttf', path=HANGANG('EB'), body_h=21, outline=True),
}
