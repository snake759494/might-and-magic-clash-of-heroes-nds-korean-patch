"""폰트 한 개에 한글 범위를 추가한다."""
import functools
from PIL import ImageFont
import hfont
from fontcfg import CFG


@functools.lru_cache(None)
def ttf_size(path, body_h):
    # '한' 등 한글 세로 잉크 높이가 body_h 가 되는 최대 크기
    best = 6
    for size in range(6, 60):
        f = ImageFont.truetype(str(path), size)
        l, t, r, b = f.getbbox('가각힘')
        if b - t <= body_h:
            best = size
    return best


def mask_for(k, ch):
    c = CFG[k]
    if c['kind'] == 'bdf':
        m, adv = hfont.bdf_mask(c['name'], ch)
        return m
    size = ttf_size(c['path'], c['body_h'])
    m, adv = hfont.ttf_mask(c['path'], size, ch)
    # 세로 크기를 body_h에 맞춘다(넘치는 행은 잘라냄)
    return m[:c['body_h']]


def korean_glyph(k, style, ch):
    c = CFG[k]
    m = mask_for(k, ch)
    h = len(m)
    body_top = style.cap_top + (1 if c['outline'] and style.outlined else 0)
    # 영문 대문자 본체 상단에 맞추고, 한글이 크면 위로 늘린다
    cap_body = style.cap_h - (2 if c['outline'] and style.outlined else 0)
    top = body_top - max(0, h - cap_body) // 2 if c['kind'] == 'bdf' else body_top - max(0, h - cap_body)
    return style.glyph(m, top, c['outline'] and style.outlined)
