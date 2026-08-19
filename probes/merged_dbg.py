import sys
sys.path.insert(0, '.')
import numpy as np
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks
import cv2

doc = open_pdf('data/deskar_catalog.pdf')
i = 31
img3, z3 = render_page(doc, i, 3.0)
img6, z6 = render_page(doc, i, 6.0)

# crop the r column area for rows 400-450
x0p, x1p, y0p, y1p = 355, 380, 410, 450
crop = img6[int(y0p*z6):int(y1p*z6), int(x0p*z6):int(x1p*z6)]
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
print('r column crop size:', crop.shape)

# light text on dark? try both
for thresh in (80, 120, 160, 200):
    bw = (gray > thresh).astype(np.uint8)
    n = int(bw.sum())
    print(f' thresh {thresh}: lit px = {n}')

# OCR the crop at high zoom
tmp = '/tmp/r_col_crop.png'
crop_big = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
cv2.imwrite(tmp, crop_big)
from converter.ocr_engine import get_ocr
res = get_ocr().ocr(tmp, cls=False)
print('OCR result:')
if res and res[0]:
    for line in res[0]:
        box = [[int(x) for x in pt] for pt in line[0]]
        text, conf = line[1]
        xs=[pt[0] for pt in box]; ys=[pt[1] for pt in box]
        print(f'  [{min(xs)},{min(ys)} {max(xs)},{max(ys)}] {conf:.2f} {text!r}')