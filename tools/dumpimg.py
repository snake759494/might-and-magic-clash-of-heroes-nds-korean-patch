import sys, json, numpy as np
sys.path.insert(0, 'tools')
from PIL import Image, ImageDraw
import romio, gfx, cel
from palmatch import index_image
r = romio.load(); nm = romio.names(r)
mp = json.load(open('work/palmatch.json')); cp = json.load(open('work/celpal.json'))
def pal(n):
    p = romio.palette(romio.get(r, nm, n)); return np.array(p + [(255, 0, 255)] * (256 - len(p)), np.uint8)
tiles = []
for k, pn in cp.items():
    if not pn: continue
    P = pal(pn); _, ims = cel.find_images(romio.get(r, nm, f'res/art/{k}.cel'))
    for j, (s, x, y, w, h, px) in enumerate(ims):
        if w * h < 64: continue
        a = cel.untile(px, w, h); im = P[a].copy(); im[a == 0] = (40, 40, 40)
        tiles.append((f'cel{k}_{j}', Image.fromarray(im)))
# 시트: 칸 160x140
W, H, C = 200, 140, 8
for s in range(0, len(tiles), C * 7):  # 시트당 56장
    sh = Image.new('RGB', (W * C, H * 7), (20, 20, 20)); d = ImageDraw.Draw(sh)
    for i, (n, im) in enumerate(tiles[s:s + C * 7]):
        f = max(1, min((W - 4) // im.width, (H - 14) // im.height)); im = im.resize((im.width * f, im.height * f), 0); im.thumbnail((W - 4, H - 14)); x, y = i % C * W, i // C * H
        sh.paste(im, (x + 2, y + 12)); d.text((x + 2, y), n, fill=(255, 255, 0))
    sh.save(f'work/img/c{s // (C * 7):03d}.png')
json.dump([n for n, _ in tiles], open('work/img/index.json', 'w'))
print(len(tiles), (len(tiles) + 55) // 56)
