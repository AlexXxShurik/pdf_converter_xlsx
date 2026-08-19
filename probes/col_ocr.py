import logging, sys
logging.disable(logging.WARNING)
import pymupdf
import cv2
import numpy as np
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
doc = pymupdf.open('data/deskar_catalog.pdf')
page = int(sys.argv[1])
zoom = 6.0
p = doc[page]
pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
else:
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

cx = float(sys.argv[2])
y0, y1 = int(198 * zoom), int(252 * zoom)
x0, x1 = int((cx - 7) * zoom), int((cx + 7) * zoom)
crop = img[y0:y1, x0:x1]
big = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
rot = cv2.rotate(big, cv2.ROTATE_90_CLOCKWISE)
cv2.imwrite('/tmp/col.png', rot)
res = ocr.ocr('/tmp/col.png', cls=False)
print(f'column x~{cx}:')
if res and res[0]:
    for line in res[0]:
        print('  ', repr(line[1][0]), line[1][1])