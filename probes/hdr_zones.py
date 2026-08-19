import sys
import cv2
import numpy as np
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks

doc = open_pdf('data/AccKee2025.pdf')
i = int(sys.argv[1]) if len(sys.argv) > 1 else 3
z = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
img, _ = render_page(doc, i, z)
print('img shape', img.shape)

# 4 зоны заголовков по x (pt): ~60-340, 360-570, 640-880, 900-1100
zones = [(60, 345), (355, 575), (635, 885), (895, 1130)]
for (x0, x1) in zones:
    region = img[int(198*z):int(212*z), int(x0*z):int(x1*z)]
    region = cv2.resize(region, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    blocks = ocr_blocks(region, z * 1.5, x0p=x0, y0p=198.0)
    print(f'--- header zone x {x0}-{x1} ---')
    for b in sorted(blocks, key=lambda b: (b['cy'], b['cx'])):
        print('%.1f %.1f %r' % (b['cy'], b['cx'], b['text']))
