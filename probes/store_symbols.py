import sys
import cv2
import numpy as np
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks

doc = open_pdf('data/AccKee2025.pdf')
i = 3
img6, z6 = render_page(doc, i, 6.0)
gray = cv2.cvtColor(img6, cv2.COLOR_BGR2GRAY)

# левая таблица: Store колонка x~168, данные y 220..790
# Проверим пиксели в зоне Store (x 163..176) для каждого ряда модели
rows_y = [231, 242, 253, 264, 275, 286, 297, 308, 319, 330, 341, 352, 363, 374,
          385, 396, 407, 418, 429, 440, 451, 462, 473, 484, 495, 506, 517, 528,
          539, 550, 561, 572, 583, 594, 605, 616, 627, 638, 649, 660, 671, 682,
          693, 704, 715, 726, 737, 748, 759, 770]
for ry in rows_y:
    x0, x1 = int(162*z6), int(178*z6)
    y0, y1 = int((ry-4)*z6), int((ry+4)*z6)
    sub = gray[y0:y1, x0:x1]
    _, bw = cv2.threshold(sub, 150, 255, cv2.THRESH_BINARY_INV)
    cnts, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    desc = []
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if area < 8:
            continue
        (cx, cy), r = cv2.minEnclosingCircle(cnt)
        fill = area / (np.pi * r * r)
        desc.append('r=%.1f fill=%.2f' % (r, fill))
    print(ry, ' | '.join(desc) if desc else 'EMPTY')
