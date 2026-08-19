import logging, sys
logging.disable(logging.WARNING)
import pymupdf
import cv2
import numpy as np
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
doc = pymupdf.open('data/deskar_catalog.pdf')
page = int(sys.argv[1])
zoom = float(sys.argv[2])
x0p = float(sys.argv[3]); x1p = float(sys.argv[4])
y0p = float(sys.argv[5]); y1p = float(sys.argv[6])

p = doc[page]
pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
else:
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

x0, x1 = int(x0p * zoom), min(int(x1p * zoom), pix.width)
y0, y1 = int(y0p * zoom), min(int(y1p * zoom), pix.height)
crop = img[y0:y1, x0:x1]
big = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

for rot in [0, 90, 270]:
    r = big if rot == 0 else cv2.rotate(big, cv2.ROTATE_90_CLOCKWISE if rot == 90 else cv2.ROTATE_90_COUNTERCLOCKWISE)
    tmp = f'/tmp/rot_{rot}.png'
    cv2.imwrite(tmp, r)
    res = ocr.ocr(tmp, cls=False)
    print(f'--- rot {rot} ---')
    if res and res[0]:
        for line in sorted(res[0], key=lambda l: (min(pt[1] for pt in l[0]), min(pt[0] for pt in l[0]))):
            box = line[0]
            xs = [int(pt[0]) for pt in box]; ys = [int(pt[1]) for pt in box]
            text, conf = line[1]
            print(f'  [{min(xs):4d}-{max(xs):4d} {min(ys):4d}-{max(ys):4d}] {conf:.2f} {text!r}')