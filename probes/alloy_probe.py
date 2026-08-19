import logging, sys
logging.disable(logging.WARNING)
import pymupdf
import cv2
import numpy as np
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
doc = pymupdf.open('data/deskar_catalog.pdf')
page = int(sys.argv[1]) if len(sys.argv) > 1 else 22
zoom = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
x0p = float(sys.argv[3]) if len(sys.argv) > 3 else 420
x1p = float(sys.argv[4]) if len(sys.argv) > 4 else 580
y0p = float(sys.argv[5]) if len(sys.argv) > 5 else 390
y1p = float(sys.argv[6]) if len(sys.argv) > 6 else 1620

p = doc[page]
mat = pymupdf.Matrix(zoom, zoom)
pix = p.get_pixmap(matrix=mat)
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
else:
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

x0, x1 = int(x0p * zoom), int(x1p * zoom)
y0, y1 = int(y0p * zoom), int(y1p * zoom)
x1 = min(x1, pix.width); y1 = min(y1, pix.height)
crop = img[y0:y1, x0:x1]
scale = 2.0
crop_big = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
tmp = '/tmp/alloy_zone.png'
cv2.imwrite(tmp, crop_big)

res = ocr.ocr(tmp, cls=False)
if res and res[0]:
    for line in sorted(res[0], key=lambda l: (min(pt[1] for pt in l[0]), min(pt[0] for pt in l[0]))):
        box = line[0]
        xs = [int(pt[0]) for pt in box]; ys = [int(pt[1]) for pt in box]
        text, conf = line[1]
        # convert back to pt coordinates
        px0, px1 = x0p + min(xs) / (zoom * scale), x0p + max(xs) / (zoom * scale)
        py0, py1 = y0p + min(ys) / (zoom * scale), y0p + max(ys) / (zoom * scale)
        print(f'[{px0:6.1f}-{px1:6.1f} {py0:6.1f}-{py1:6.1f}] {conf:.2f} {text!r}')