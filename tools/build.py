"""한글 ROM 빌드: 영어(.en) 로케일을 한국어로 교체하고 폰트에 한글 범위를 추가한다.

한글 음절은 U+0100부터 순서대로 재배정한다(상위바이트 1.. 범위, 하위바이트가 글리프 색인).
"""
import sys, json, re, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import romio, lz11, fontlib, hfont, kfont, loctext

ROOT = romio.ROOT
OUT = ROOT / 'Might & Magic - Clash of Heroes (Korean).nds'
HANGUL = re.compile('[가-힣]')
SMALL = [int(x) for x in os.environ['SMALL'].split(',') if x] if 'SMALL' in os.environ else [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13]

LARGE = [int(x) for x in os.environ['LARGE'].split(',') if x] if 'LARGE' in os.environ else [14, 15, 16, 17, 18, 19, 20, 22]
LABEL_MAX = 24
# 글꼴 22(대형 제목)는 메모리 여유가 적어 제목류 문자열 음절만 넣는다: (파일, 시작, 끝)
MENU_SETS = [('0', 164, 208), ('0', 334, 348), ('10', 0, 43)]
TITLE_SETS = [('0', 142, 143), ('0', 230, 233), ('0', 262, 264), ('0', 313, 318), ('0', 355, 361), ('0', 371, 371), ('8', 0, 2), ('8', 6, 12), ('8', 31, 31), ('8', 59, 59)]


def load_ko():
    ko = {}
    for p in sorted((ROOT / 'translation/src').glob('*.json')):
        src = json.loads(p.read_text(encoding='utf8'))
        kp = ROOT / 'translation/ko' / p.name
        if 'KOFILES' in os.environ and p.stem not in os.environ['KOFILES'].split(','):
            kp = ROOT / 'nonexistent'
        tr = json.loads(kp.read_text(encoding='utf8')) if kp.exists() else {}
        ko[p.stem] = [tr.get(k, v) for k, v in src.items()]
    return ko


def main():
    r = romio.load(); nm = romio.names(r)
    ko = load_ko()
    allsyl = sorted({c for L in ko.values() for s in L for c in HANGUL.findall(s)})
    labels = {c for L in ko.values() for s in L if len(s) <= LABEL_MAX for c in HANGUL.findall(s)}
    # 부분 집합만 담는 글꼴의 범위 테이블에 빈 칸이 덜 생기도록 사용처가 좁은 음절부터 앞 코드에 배정
    emb = {c for i in EMB_STRINGS for c in HANGUL.findall(ko['0'][i])}
    title = {c for f_, a, b in TITLE_SETS for i, t in enumerate(ko[f_]) if a <= i <= b for c in HANGUL.findall(t)}
    menu = {c for f_, a, b in MENU_SETS for i, t in enumerate(ko[f_]) if a <= i <= b and len(t) <= LABEL_MAX for c in HANGUL.findall(t)}
    sys_ = {c for f_ in ('0', '8', '9') for t in ko[f_] for c in HANGUL.findall(t)}
    ui = {c for f_ in ko if f_ == '0' or 7 <= int(f_) <= 35 for t in ko[f_] for c in HANGUL.findall(t)}
    allsyl.sort(key=lambda c: (c not in emb, c not in title, c not in menu, c not in sys_, c not in ui, c))
    code = {c: 0x100 + i for i, c in enumerate(allsyl)}
    print('음절', len(allsyl), '라벨 음절', len(labels))

    for n, L in ko.items():
        enc = [''.join(chr(code[c]) if c in code else c for c in s) for s in L]
        oo = loctext.offsets(romio.get(r, nm, f'res/locales/{n}.en'))
        r.files[nm[f'res/locales/{n}.en']] = lz11.compress(loctext.build(enc, oo))

    sizes = {}
    global ERR_CODE
    ERR_CODE = {c: 0x80 + i for i, c in enumerate(sorted({c for t in ERR_TEXT.values() for c in HANGUL.findall(t)}))}
    assert len(ERR_CODE) <= 0x20
    def syl(sel):
        """sel: [(파일, 시작, 끝, 최대길이)] → 해당 문자열 음절 집합"""
        return {c for f_, a_, b_, mx in sel for i, t in enumerate(ko[f_]) if a_ <= i <= b_ and len(t) <= mx for c in HANGUL.findall(t)}
    ALL = [(f_, 0, 9999, 9999) for f_ in ko]
    R = lambda f_, a_=0, b_=9999, mx=9999: (str(f_), a_, b_, mx)
    # 메모리 여유가 적어 폰트마다 실제로 그리는 문자열의 음절만 넣는다(훅으로 화면별 사용 폰트 확인).
    PAUSE = [R(0, 145, 146), R(0, 156, 157), R(0, 209, 221), R(0, 298, 300), R(0, 367, 372), R(0, 391, 393)]
    SYSMSG = PAUSE + [R(0, 142, 163), R(0, 222, 261), R(0, 298, 303), R(0, 330, 333), R(0, 344, 352),
                      R(0, 362, 393)]
    PANEL = [R(0, 230, 240), R(0, 313, 333), R(0, 353, 354), R(9), R(10, 0, 9)]
    TITLE = [R(0, 355, 361), R(0, 371, 371), R(8, 0, 2), R(8, 6, 12), R(8, 31, 31)]
    RESULT = [R(0, 142, 144), R(0, 158, 159), R(0, 224, 224), R(0, 230, 240), R(0, 262, 265), R(0, 313, 333), R(0, 353, 354)]
    NAMES = RESULT + [R(8, 31, 31), R(0, 164, 208, LABEL_MAX)] + [R(f_, 0, 9999, LABEL_MAX) for f_ in (10, 12, 14, 17, 19, 22, 24, 27, 29, 32, 34)]
    DESC = [R(0, 262, 297)] + [R(f_) for f_ in range(10, 36) if f_ not in (11, 16, 21, 26, 31)]
    UI = [R(0)] + [R(f_) for f_ in range(7, 36)]
    # 인물 이름표·획득 팝업: 인물/유닛 이름(유닛 파일 0~10번 = 유닛 이름·등급)
    PEOPLE = [R(0, 0, 141), R(0, 150, 154), R(0, 164, 208), R(10, 0, 9)] + [R(f_, 0, 10) for f_ in (14, 19, 24, 29, 34)]
    ABIL = [R(f_, 0, 9999, LABEL_MAX) for f_ in (14, 19, 24, 29, 34)]  # 유닛 카드: 등급·능력 이름
    TUT = [R(1)] + [R(f_) for f_ in range(36, 54)] + [R(0, 155, 163), R(0, 363, 366)]
    MENU = [R(8), R(9)] + [(f_, a_, b_, LABEL_MAX) for f_, a_, b_ in MENU_SETS + TITLE_SETS]
    ROLE = {0: ALL, 1: DESC, 2: SYSMSG + PEOPLE, 3: PAUSE, 4: SYSMSG + RESULT, 5: SYSMSG + RESULT, 6: SYSMSG + RESULT, 7: SYSMSG + RESULT, 13: TUT,
            8: PANEL + ABIL, 9: PANEL + ABIL, 14: NAMES, 15: NAMES, 16: NAMES, 22: TITLE + [R(0, 313, 318)],
            17: MENU, 18: MENU, 19: MENU, 20: MENU}
    for k in SMALL + LARGE:
        f = fontlib.Font(romio.get(r, nm, f'res/art/{k}.font')); st = hfont.Style(f)
        need = syl(ROLE[k])
        chars = [c for c in allsyl if c in need]
        if True:
            # 한국어 모드에서 쓰지 않는 라틴 확장 글자(악센트 등)를 비워 메모리를 확보한다.
            # 버튼 아이콘(0xA5~0xBD)은 유지. 14~16은 언어 선택의 Français/Español 표기에 쓰여 유지.
            for cp in list(range(0x7F, 0xA5)) + list(range(0xBE, 0x100)):
                if cp - 0x21 < len(f.glyphs) and not (k in (14, 15, 16) and chr(cp) in 'çñ'):
                    f.glyphs[cp - 0x21][4] = None
        if k in SMALL:
            # ARM9 고정 문구용 1바이트 코드(0x80~)
            for c, cp in ERR_CODE.items():
                f.glyphs[cp - 0x21] = kfont.korean_glyph(k, st, c)
        for c in chars:
            cp = code[c]; hi, lo = cp >> 8, cp & 0xFF
            rng = f.ranges.setdefault(hi, [])
            while len(rng) <= lo:
                rng.append([0, 0, 0, 0, None])
            g = kfont.korean_glyph(k, st, c)

            rng[lo] = g
        # 게임의 글리프 조회는 `하위바이트 <= 개수`로 검사해 범위 바로 다음 코드에서 테이블 밖을 읽는다.
        # 쓰는 범위는 끝(256칸, 마지막 범위는 전체 최대 코드+1)까지 빈 칸으로 채워 그런 코드가 생기지 않게 한다.
        maxcode = 0x100 + len(allsyl) - 1
        for hi, rng in f.ranges.items():
            if hi == 0:
                continue
            full = 256 if hi < (maxcode >> 8) else (maxcode & 0xFF) + 2
            while len(rng) < full:
                rng.append([0, 0, 0, 0, None])
        if k != 22:
            # 한글 자간: 외곽선 없는 글리프는 1px 투명 틈, 외곽선 글리프는 외곽선끼리 겹치지 않게.
            # 글리프에 빈 열을 붙이면 메모리가 늘어 폰트 헤더의 자간 값으로 맞춘다(영문도 같이 넓어짐).
            outlined = kfont.CFG[k]['outline'] and st.outlined
            f.spacing = max(f.spacing, 1 if outlined else 2)
        raw = f.build(); sizes[k] = len(raw)
        r.files[nm[f'res/art/{k}.font']] = lz11.compress(raw)
    patch_arm9_font(r, nm, ko, code)
    patch_arm9_text(r)
    import gfxpatch; gfxpatch.apply(r, nm)
    print('폰트 크기(KB)', {k: v // 1024 for k, v in sizes.items()})
    r.saveToFile(str(OUT))
    (ROOT / 'work/charmap.json').write_text(json.dumps({c: hex(v) for c, v in code.items()}, ensure_ascii=False), encoding='utf8')
    print('저장', OUT.name)


EMB_STRINGS = range(241, 254)  # 타이틀 안내·통신 상태(글꼴 0)
NAME_0FONT = 0x20E6894  # ARM9: 요청 이름이 "0.font"이면 내장 사본을 쓰는 비교 문자열


# ARM9 고정 문구(언어별 char* 표의 영어 슬롯): 주소 → 한국어. 원래 슬롯 크기 안에 맞춘다.
ERR_TEXT = {0x20DA2C8: '불러오는 중...', 0x20DA324: '전원을 꺼 주십시오.', 0x20DA3A0: '무선 통신 오류입니다.'}
ERR_CODE = {}


def pad_cols(k, f, st):
    """한글 글자 사이 틈: 외곽선 없는 글리프는 1px 투명 틈, 외곽선 글리프는 외곽선끼리 겹치지 않게.
    진행폭 = 글리프 폭 + 폰트 자간이므로 오른쪽 빈 열 수로 맞춘다."""
    if k == 22:
        return 0  # 제목 전용 큰 글꼴: 메모리 여유가 없어 원래 자간 유지
    outlined = kfont.CFG[k]['outline'] and st.outlined
    return max(0, (0 if outlined else 1) - f.spacing)


def pad_right(g):
    """글리프 오른쪽에 투명 열 1px을 붙여 진행폭을 1 늘린다."""
    w, h, x, y, px = g
    rows = [px[i * w:(i + 1) * w] + bytes(1) for i in range(h)]
    return [w + 1, h, x, y, b''.join(rows)]


def patch_arm9_text(r):
    a = bytearray(r.arm9)
    for addr, t in ERR_TEXT.items():
        o = addr - 0x2000000
        n = a.index(0, o) - o  # 원래 문자열 길이
        b = bytes(ERR_CODE[c] if c in ERR_CODE else ord(c) for c in t)
        assert len(b) <= n, (t, len(b), n)
        a[o:o + n] = b + bytes(n - len(b))
    r.arm9 = bytes(a)


def patch_arm9_font(r, nm, ko, code):
    """ARM9 내장 0.font 사본은 무결성 검사 영역이라 수정할 수 없다. 비교 문자열을 바꿔
    게임이 한글이 추가된 res/art/0.font 파일을 읽게 한다."""
    a = bytearray(r.arm9); o = NAME_0FONT - 0x2000000
    assert a[o:o + 7] == bytes(b'0.font') + bytes(1)
    a[o:o + 7] = bytes(b'0.fon#') + bytes(1)
    r.arm9 = bytes(a)


if __name__ == '__main__':
    main()
