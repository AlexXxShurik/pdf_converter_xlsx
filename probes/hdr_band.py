import sys
import cv2
import numpy as np
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks

doc = open_pdf('data/AccKee2025.pdf')
i = int(sys.argv[1]) if len(sys.argv) > 1 else 3
z = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
img, _ = render_page(doc, i, z)
print('img shape', img.shape)

# заголовки в pt примерно y 195..215 → px
y0, y1 = int(195 * z), int(215 * z)
band = img[y0:y1, :]
big = cv2.resize(band, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
blocks = ocr_blocks(big, z * 2, y0p=195.0)
print('--- header band blocks (y 195-215) ---')
for b in sorted(blocks, key=lambda b: (b['cy'], b['cx'])):
    print('%.1f %.1f %r' % (b['cy'], b['cx'], b['text']))
