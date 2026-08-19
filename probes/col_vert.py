import logging, sys
logging.disable(logging.WARNING)
import pymupdf
import cv2
import numpy as np

doc = pymupdf.open('data/deskar_catalog.pdf')
page = int(sys.argv[1])
zoom = 12.0
x0p = float(sys.argv[2]); x1p = float(sys.argv[3])

p = doc[page]
pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
else:
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

x0, x1 = int(x0p * zoom), int(x1p * zoom)
y0, y1 = int(200 * zoom), int(252 * zoom)
gray = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
bright = (gray > 140).astype(np.uint8)
h, w = bright.shape
# print column-major: for each source x (which holds a vertical char column), print as a row block
# instead: print rows of y, columns of x (vertical text appears, chars stacked downward)
stepx = max(1, w // 60)
stepy = max(1, h // 110)
for ry in range(0, h, stepy):
    row = ''
    for rx in range(0, w, stepx):
        block = bright[ry:ry+stepy, rx:rx+stepx]
        lit = (block > 0).mean()
        if lit > 0.4:
            row += '#'
        elif lit > 0.1:
            row += '+'
        else:
            row += ' '
    print(row)