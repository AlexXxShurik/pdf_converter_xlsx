import logging, sys
logging.disable(logging.WARNING)
import pymupdf
import cv2
import numpy as np

doc = pymupdf.open('data/deskar_catalog.pdf')
page = int(sys.argv[1])
zoom = 8.0
p = doc[page]
pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
else:
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
y0, y1 = int(202 * zoom), int(246 * zoom)
band = gray[y0:y1]
# bright text: > 140
bright = (band > 140).astype(np.uint8)
colsum = bright.sum(axis=0)
thr = colsum.max() * 0.25
cols = []
in_c = False
start = 0
for i in range(len(colsum)):
    if colsum[i] > thr and not in_c:
        in_c = True; start = i
    elif colsum[i] <= thr and in_c:
        in_c = False; cols.append((start, i))
if in_c:
    cols.append((start, len(colsum)))
print('columns (px, pt):')
for a, b in cols:
    if b - a < 8: continue
    print(f'  px {a}-{b}  pt {a/zoom:.1f}-{b/zoom:.1f}  center { (a+b)/2/zoom:.1f}')