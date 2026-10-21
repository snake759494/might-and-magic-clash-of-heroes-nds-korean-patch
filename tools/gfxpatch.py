"""이미지 속 영문 한글화. build.py에서 apply(r, nm)을 호출한다. 단독 실행 시 미리보기 생성."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import romio, lz11, cel, imgedit as ie

G7 = ('bdf', 'Galmuri7', 1, 0)
G9 = ('bdf', 'Galmuri9', 1, 0)
G14B = ('bdf', 'Galmuri14', 2, 1)

# 전투 배너: (셀, 프레임별 문구)
FRAMES = {
    262: (['아군 턴', '적 턴', '승리!', '패배', '영웅 주문'], False),
    132: (['레벨 업'] * 9, True),
}

# 영역 교체: (셀, 이미지, 영역 또는 None=전체, [줄...], 글꼴, 옵션)
REGIONS = [
    (130, 0, None, ['대기'], G7, {}),
    *[(130, i, None, [f'{i}턴'], G7, {}) for i in range(1, 10)],
    (130, 10, None, ['0턴'], G7, {}),
    (396, 9, (0, 19, 32, 29), ['장착'], G7, {}),
    (345, 30, (5, 0, 22, 7), ['장착'], G7, {'bg': 1, 'outline': False, 'fill': 0x8}),
    (52, 0, (2, 23, 24, 32), ['여관'], G7, {'bg': 4, 'outline': False}),
    (84, 0, None, ['지하묘지'], G7, {'outline': False}),
    (85, 0, None, ['도시', '폐허'], G7, {'outline': False}),
    (86, 0, None, ['죽음', '교단', '의식'], G7, {'outline': False, 'gap_y': 1}),
    (87, 0, None, ['영원의', '납골당'], G7, {'outline': False}),
    (88, 0, None, ['루드밀라의', '성역'], G7, {'outline': False}),
    (89, 1, None, ['영원한', '성소'], G7, {'outline': False}),
    (90, 1, None, ['투기장'], G7, {'outline': False}),
    (91, 1, None, ['오염된', '모래땅'], G7, {'outline': False}),
    (92, 1, None, ['오염된', '모래땅'], G7, {'outline': False}),
]


def patch_cels(r, nm, previews=None):
    changed = {}
    def get(k):
        if k not in changed:
            changed[k] = romio.get(r, nm, f'res/art/{k}.cel')
        return changed[k]
    for k, (texts, keep) in FRAMES.items():
        d = get(k); new = {}
        for fr, t in enumerate(texts):
            new.update(ie.retext_frame(d, fr, t, G14B, new, keep_other=keep))
        if previews is not None:
            _, ims = cel.find_images(d)
            previews += [cel.untile(ims[i][5], ims[i][3], ims[i][4]) for i in sorted(new)] + [new[i] for i in sorted(new)]
        changed[k] = ie.write_images(d, new)
    for k, j, box, lines, spec, opt in REGIONS:
        d = get(k); _, ims = cel.find_images(d)
        s, x, y, w, h, px = ims[j]
        a = cel.untile(px, w, h).copy(); before = a.copy()
        ie.retext_region(a, box or (0, 0, w, h), lines, spec, **opt)
        if previews is not None:
            previews += [before, a]
        changed[k] = ie.write_images(d, {j: a})
    for k, d in changed.items():
        r.files[nm[f'res/art/{k}.cel']] = lz11.compress(d)
    return changed


# 배경 맵 라벨: (맵, 팔레트 파일, [(영역, 종류, [줄], 글꼴)])
G11B = ('bdf', 'Galmuri11-Bold', 1, 0)
MAPS = {
    338: ('pal_map338.json', [
        ((3, 7, 70, 26), 'light', ['아샨'], G14B),
        ((58, 48, 118, 62), 'light', ['이롤란'], G11B),
        ((115, 66, 209, 89), 'light', ['신성 그리핀', '제국'], G11B),
        ((68, 142, 160, 165), 'light', ['은빛 도시'], G11B),
        ((165, 140, 218, 154), 'light', ['헤레시'], G11B),
        ((0, 57, 46, 69), 'dark', ['이리수스 해'], G7),
        ((26, 174, 86, 187), 'dark', ['야만의 바다'], G7),
        ((193, 163, 235, 184), 'dark', ['비취', '대양'], G7),
    ]),
    1: ('pal_map1.json', [
        ((0, 130, 256, 190), 'solid', ['마이트 앤 매직® 클래시 오브 히어로즈®',
                                      '© 2009 Ubisoft Entertainment. 모든 권리 보유.',
                                      'Might and Magic, Heroes, Ubisoft 및 Ubisoft 로고는',
                                      '미국 및 기타 국가에서 Ubisoft Entertainment의',
                                      '상표입니다.'], G9),
    ]),
}


def patch_maps(r, nm, previews=None):
    import json
    import mapedit as me
    gdir = Path(__file__).resolve().parents[1] / 'translation/gfx'
    for k, (pf, labels) in MAPS.items():
        if not (gdir / pf).exists():
            print('  지도 팔레트 없음, 건너뜀:', pf)  # 원작 화면에서 복원한 팔레트(저장소 미포함)
            continue
        P = np.array(json.load(open(gdir / pf)), np.uint8)
        a = me.load_index(r, nm, str(k)); before = a.copy()
        used = set(np.unique(a).tolist())
        lum = P[a].astype(int) @ np.array([30, 59, 11]) // 100
        for (x0, y0, x1, y1), kind, lines, spec in labels:
            box = np.zeros(a.shape, bool); box[y0:y1, x0:x1] = True
            if kind == 'light':
                m = box & (lum > 165); er = (me.dilate(m, 2) | (me.dilate(m, 4) & (lum < 120))) & me.dilate(box, 2)
                fill = me.nearest_index(P, (240, 240, 240), used); shadow = me.nearest_index(P, (20, 30, 60), used)
            elif kind == 'auto':
                # 배경 = 영역 최다 색인, 글자 = 배경과 밝기 차가 큰 픽셀의 최다 색인, 외곽선 = 그 주변 최다 색인
                bgv = int(np.bincount(a[box]).argmax()); bl = int(P[bgv].astype(int) @ [30, 59, 11] // 100)
                txt = box & (np.abs(lum - bl) > 60)
                fill = int(np.bincount(a[txt]).argmax()) if txt.any() else bgv
                ring = me.dilate(txt, 1) & ~txt & box
                cand = np.bincount(a[ring], minlength=256); cand[bgv] = 0; cand[fill] = 0
                shadow = int(cand.argmax()) if cand.max() > 0 else None
                er = None
                # 영역 안 글자와 외곽선만 배경색으로 지우고(무늬 보존을 위해 inpaint) 새 글자를 그린다
                a = me.inpaint(a, me.dilate(txt, 1) & box)
            elif kind == 'solid':
                bgv = int(np.bincount(a[box]).argmax())
                fill = me.nearest_index(P, (255, 255, 255), used); shadow = None
                er = None; a[box] = bgv
            else:
                m = box & (lum < 95); er = me.dilate(m, 1) & box
                fill = me.nearest_index(P, (35, 55, 100), used); shadow = None
            if er is not None:
                a = me.inpaint(a, er)
            tm = ie.lines_mask(lines, spec, 1)
            H, W = tm.shape
            oy = y0 + (y1 - y0 - H) // 2; ox = max(0, x0 + (x1 - x0 - W) // 2)
            full = np.zeros(a.shape, bool)
            full[oy:oy + H, ox:ox + W] = tm[:a.shape[0] - oy, :a.shape[1] - ox]
            if shadow is not None and kind == 'auto':
                a[me.dilate(full, 1) & ~full] = shadow
            elif shadow is not None:
                sh = np.zeros_like(full); sh[1:, 1:] = full[:-1, :-1]
                a[sh & ~full] = shadow
            a[full] = fill
        if previews is not None:
            previews.append((k, P, before, a))
        setd, mapd = me.rebuild(r, nm, str(k), a)
        r.files[nm[f'res/art/{k}.set']] = lz11.compress(setd)
        r.files[nm[f'res/art/{k}.map']] = lz11.compress(mapd)


# 언어 선택(378)·메인 메뉴 아이콘(372)의 미국 국기 → 태극기. 팔레트는 해당 화면의 2.pal
FLAGS = [(378, 0), (378, 1), (372, 0), (372, 5)]


def patch_flags(r, nm, previews=None):
    import flag
    p = romio.palette(romio.get(r, nm, 'res/art/2.pal'))
    P = np.array((p + [(255, 0, 255)] * 256)[:256], np.uint8)
    for k in sorted({k for k, j in FLAGS}):
        d = romio.get(r, nm, f'res/art/{k}.cel'); _, ims = cel.find_images(d); new = {}
        for kk, j in FLAGS:
            if kk != k: continue
            s0, x, y, w, h, px = ims[j]
            a = cel.untile(px, w, h); new[j] = flag.replace_us_flag(a, P)
            if previews is not None: previews += [a, new[j]]
        r.files[nm[f'res/art/{k}.cel']] = lz11.compress(ie.write_images(d, new))


def apply(r, nm):
    patch_cels(r, nm)
    patch_flags(r, nm)
    patch_maps(r, nm)


if __name__ == '__main__':
    r = romio.load(); nm = romio.names(r); pv = []
    patch_cels(r, nm, pv)
    ie.preview_pairs(pv, 'work/gfx_preview.png', 3)
    mp = []; patch_maps(r, nm, mp)
    from PIL import Image
    for k, P, b, a in mp:
        sh = Image.new('RGB', (512, a.shape[0]))
        sh.paste(Image.fromarray(P[b]), (0, 0)); sh.paste(Image.fromarray(P[a]), (256, 0))
        sh.resize((1024, a.shape[0] * 2), 0).save(f'work/map_preview_{k}.png')
    print('미리보기', len(pv), len(mp))
