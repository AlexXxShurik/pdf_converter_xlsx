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
# upscale, grayscale, denoise, adaptive threshold for better OCR
crop_big = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
gray = cv2.cvtColor(crop_big, cv2.COLOR_BGR2GRAY)
bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 15)
tmp = '/tmp/badge.png'
cv2.imwrite(tmp, crop_big)
tmp2 = '/tmp/badge_bw.png'
cv2.imwrite(tmp2, bw)

for tag, f in [('color', tmp), ('bw', tmp2)]:
    res = ocr.ocr(f, cls=False)
    print(f'--- {tag} ---')
    if res and res[0]:
        for line in sorted(res[0], key=lambda l: (min(pt[1] for pt in l[0]), min(pt[0] for pt in l[0]))):
            box = line[0]
            xs = [int(pt[0]) for pt in box]; ys = [int(pt[1]) for pt in box]
            text, conf = line[1]
            px0 = x0p + min(xs) / (zoom * 3); px1 = x0p + max(xs) / (zoom * 3)
            py0 = y0p + min(ys) / (zoom * 3); py1 = y0p + max(ys) / (zoom * 3)
            print(f'  [{px0:6.1f}-{px1:6.1f} {py0:6.1f}-{py1:6.1f}] {conf:.2f} {text!r}')