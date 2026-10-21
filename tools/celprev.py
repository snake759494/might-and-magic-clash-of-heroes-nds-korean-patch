"""셀 이미지를 역할색으로 확대 미리보기: celprev.py out.png 셀_이미지 ..."""
import sys
sys.path.insert(0, 'tools')
import romio, cel, imgedit
r = romio.load(); nm = romio.names(r); arrs = []
for t in sys.argv[2:]:
    k, j = t.split('_'); _, ims = cel.find_images(romio.get(r, nm, f'res/art/{k}.cel'))
    s, x, y, w, h, px = ims[int(j)]; arrs.append(cel.untile(px, w, h))
imgedit.preview(arrs, sys.argv[1], int(sys.argv[1].split('.')[0][-1]) if sys.argv[1][-5].isdigit() else 3)
