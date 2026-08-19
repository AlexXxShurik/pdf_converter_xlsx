import logging, sys
logging.disable(logging.WARNING)
import pymupdf
import cv2
import numpy as np

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
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
# binarize: text dark on light? or light on colored bg?
_, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

h, w = bw.shape
# downsample to printable grid ~ 120 cols
stepx = max(1, w // 120)
stepy = max(1, h // 60)
for ry in range(0, h, stepy):
    row = ''
    for rx in range(0, w, stepx):
        block = bw[ry:ry+stepy, rx:rx+stepx]
        dark = (block < 128).mean()
        if dark > 0.5:
            row += '#'  # dark
        elif dark > 0.15:
            row += '+'  # mid
        else:
            row += ' '
    print(row)