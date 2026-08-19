import sys
import cv2
import numpy as np
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks

doc = open_pdf('data/AccKee2025.pdf')
i = 3
z = 5.0
img, _ = render_page(doc, i, z)

# широкие зоны, чтобы поймать Dc/Ds слева от Specification/Item
zones = [(350, 600), (630, 890), (890, 1140)]
for (x0, x1) in zones:
    region = img[int(198*z):int(215*z), int(x0*z):int(x1*z)]
    region = cv2.resize(region, None, fx=1.4, fy=1.4, interpolation=cv2.INTER_CUBIC)
    blocks = ocr_blocks(region, z * 1.4, x0p=x0, y0p=198.0)
    print(f'--- zone x {x0}-{x1} ---')
    for b in sorted(blocks, key=lambda b: (b['cy'], b['cx'])):
        print('%.1f %.1f %r' % (b['cy'], b['cx'], b['text']))