import logging, sys
logging.disable(logging.WARNING)
import pymupdf
import cv2
import numpy as np
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
doc = pymupdf.open('data/deskar_catalog.pdf')
page = int(sys.argv[1])
zoom = 4.0
x0p, x1p = 365.0, 585.0
y0p, y1p = 200.0, 250.0

p = doc[page]
pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
else:
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

x0, x1 = int(x0p * zoom), min(int(x1p * zoom), pix.width)
y0, y1 = int(y0p * zoom), int(y1p * zoom)
band = img[y0:y1, x0:x1]
gray = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 5)

# column projection to find legend columns
colsum = bw.sum(axis=0)
# find vertical text columns: runs where colsum > threshold
thr = colsum.max() * 0.15
in_col = colsum > thr
cols = []
i = 0
while i < len(in_col):
    if in_col[i]:
        j = i
        while j < len(in_col) and in_col[j]:
            j += 1
        cols.append((i, j))
        i = j
    else:
        i += 1

print('legend columns (px):', [(a, b) for a, b in cols])
print('--- per-column OCR ---')
for a, b in cols:
    pad = 4
    cell = bw[max(0, a-pad):b+pad, :]
    big = cv2.resize(cell, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    rot = cv2.rotate(big, cv2.ROTATE_90_CLOCKWISE)
    cv2.imwrite('/tmp/col.png', rot)
    res = ocr.ocr('/tmp/col.png', cls=False)
    txt = []
    if res and res[0]:
        for line in res[0]:
            text, conf = line[1]
            txt.append(f'{text}({conf:.2f})')
    cx = x0p + (a + b) / 2 / zoom
    print(f'x={cx:6.1f}  {" | ".join(txt) if txt else "EMPTY"}')