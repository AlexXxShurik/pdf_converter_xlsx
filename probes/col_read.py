import logging, sys
logging.disable(logging.WARNING)
import pymupdf
import cv2
import numpy as np

doc = pymupdf.open('data/deskar_catalog.pdf')
page = int(sys.argv[1])
zoom = float(sys.argv[2])
cx = float(sys.argv[3])
w = float(sys.argv[4]) if len(sys.argv) > 4 else 16.0

p = doc[page]
pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
else:
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

x0, x1 = int((cx - w/2) * zoom), int((cx + w/2) * zoom)
y0, y1 = int(200 * zoom), int(250 * zoom)
crop = img[y0:y1, x0:x1]
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
# bright text on dark bg: threshold > 140
bw = (gray > 140).astype(np.uint8) * 255
# find text bbox in rotated frame
rot = cv2.rotate(bw, cv2.ROTATE_90_COUNTERCLOCKWISE)
colsum = (rot > 128).sum(axis=0)
nz = np.nonzero(colsum > 0)[0]
if len(nz):
    a, b = nz.min(), nz.max()
    rot = rot[:, a-2:b+3]
print(f'text cols in rotated frame: {a if len(nz) else "-"}-{b if len(nz) else "-"} (of {bw.shape})')
h, wp = rot.shape
stepx = max(1, wp // 150)
stepy = max(1, h // 32)
for ry in range(0, h, stepy):
    row = ''
    for rx in range(0, wp, stepx):
        block = rot[ry:ry+stepy, rx:rx+stepx]
        dark = (block > 128).mean()
        if dark > 0.4:
            row += '#'
        elif dark > 0.10:
            row += '+'
        else:
            row += ' '
    print(row)