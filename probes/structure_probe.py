import logging, sys
logging.disable(logging.WARNING)
import pymupdf
import cv2
import numpy as np
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
doc = pymupdf.open('data/deskar_catalog.pdf')
page = int(sys.argv[1])
zoom = 3.0
x0p, x1p, y0p, y1p = 430.0, 580.0, 190.0, 1620.0

p = doc[page]
pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
else:
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

# ---- 1) legend band: rotate 90 and OCR to get alloy codes + x positions ----
x0, x1 = int(x0p * zoom), min(int(x1p * zoom), pix.width)
y0, y1 = int(y0p * zoom), int(245 * zoom)
band = img[y0:y1, x0:x1]
big = cv2.resize(band, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
rot = cv2.rotate(big, cv2.ROTATE_90_CLOCKWISE)
cv2.imwrite('/tmp/legend_rot.png', rot)
res = ocr.ocr('/tmp/legend_rot.png', cls=False)
alloys = []
if res and res[0]:
    for line in res[0]:
        box = line[0]
        ys = [int(pt[1]) for pt in box]
        text, conf = line[1]
        t = text.strip().upper().replace(' ', '')
        if conf < 0.5 or len(t) < 3:
            continue
        # src x pt = x0p + dst_y_px/(zoom*3)
        cx = x0p + (min(ys) + max(ys)) / 2 / (zoom * 3)
        alloys.append((cx, t, conf))
alloys.sort()
print('ALLOWS (legend):')
for cx, t, c in alloys:
    print(f'  x={cx:6.1f} {t} ({c:.2f})')

# ---- 2) group labels P/M/K in band y 190-205 ----
g0 = int(187 * zoom); g1 = int(207 * zoom)
gband = img[g0:g1, x0:x1]
gbig = cv2.resize(gband, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
cv2.imwrite('/tmp/groups.png', gbig)
gres = ocr.ocr('/tmp/groups.png', cls=False)
print('GROUPS:')
if gres and gres[0]:
    for line in gres[0]:
        box = line[0]
        xs = [int(pt[0]) for pt in box]
        text, conf = line[1]
        cx = x0p + (min(xs) + max(xs)) / 2 / (zoom * 4)
        print(f'  x={cx:6.1f} {text!r} ({conf:.2f})')

# ---- 3) circles in alloy zone per row ----
# binarize alloy zone
az0 = int(245 * zoom); az1 = int(1620 * zoom)
zone = img[az0:az1, x0:x1]
gray = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)
bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 5)
# find contours that look like circles (ring-like / small round)
contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
circles = []
for cnt in contours:
    area = cv2.contourArea(cnt)
    if area < 5: continue
    (cx, cy), r = cv2.minEnclosingCircle(cnt)
    ca = np.pi * r * r
    if 0.3 < area / ca < 1.1 and 2 < r < 14:  # filled-ish round blob
        circles.append((x0p + cx / zoom, 245 + cy / zoom, r / zoom))
print(f'CIRCLES (alloy zone): {len(circles)}')
for cx, cy, r in sorted(circles, key=lambda c: (c[1], c[0])):
    print(f'  x={cx:6.1f} y={cy:6.1f} r={r:.1f}')