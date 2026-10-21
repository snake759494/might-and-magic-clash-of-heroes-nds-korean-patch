"""지정 셀들의 이미지를 확대해 한 장으로. 사용: celshow.py out.png 셀번호...  (팔레트는 celpal.json)"""
import sys, json, numpy as np
sys.path.insert(0, 'tools')
from PIL import Image, ImageDraw
import romio, cel
r = romio.load(); nm = romio.names(r); cp = json.load(open('work/celpal.json'))
out = sys.argv[1]; ims = []
for k in sys.argv[2:]:
    pn = cp.get(k)
    if not pn: continue
    p = romio.palette(romio.get(r, nm, pn)); P = np.array(p + [(255, 0, 255)] * (256 - len(p)), np.uint8)
    for j, (s, x, y, w, h, px) in enumerate(cel.find_images(romio.get(r, nm, f'res/art/{k}.cel'))[1]):
        a = cel.untile(px, w, h); im = P[a].copy(); im[a == 0] = (40, 40, 40)
        ims.append((f'{k}_{j}', Image.fromarray(im)))
W = 1200; x = y = 0; rowh = 0; places = []
for n, im in ims:
    im = im.resize((im.width * 2, im.height * 2), 0)
    if x + im.width > W: x = 0; y += rowh + 14; rowh = 0
    places.append((n, im, x, y)); x += im.width + 6; rowh = max(rowh, im.height)
sh = Image.new('RGB', (W, y + rowh + 16), (15, 15, 15)); d = ImageDraw.Draw(sh)
for n, im, x, y in places:
    sh.paste(im, (x, y + 12)); d.text((x, y), n, fill=(255, 255, 0))
sh.save(out); print(len(ims), sh.size)
