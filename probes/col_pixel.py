import logging, sys
logging.disable(logging.WARNING)
import pymupdf
import cv2
import numpy as np

doc = pymupdf.open('data/deskar_catalog.pdf')
page = int(sys.argv[1])
zoom = float(sys.argv[2])
cx = float(sys.argv[3])
w = float(sys.argv[4]) if len(sys.argv) > 4 else 13.0

p = doc[page]
pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
else:
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

x0, x1 = int((cx - w/2) * zoom), int((cx + w/2) * zoom)
y0, y1 = int(202 * zoom), int(248 * zoom)
crop = img[y0:y1, x0:x1]
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
_, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
# rotate 90 cw so vertical text becomes horizontal (top-to-bottom becomes left-to-right)
rot = cv2.rotate(bw, cv2.ROTATE_90_CLOCKWISE)
h, wpx = rot.shape
stepx = max(1, wpx // 130)
stepy = max(1, h // 40)
for ry in range(0, h, stepy):
    row = ''
    for rx in range(0, wpx, stepx):
        block = rot[ry:ry+stepy, rx:rx+stepx]
        dark = (block > 128).mean()
        if dark > 0.5:
            row += '#'
        elif dark > 0.12:
            row += '+'
        else:
            row += ' '
    if row.strip():
        print(row)