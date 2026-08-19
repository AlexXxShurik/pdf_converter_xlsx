import logging, sys
logging.disable(logging.WARNING)
import pymupdf
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
doc = pymupdf.open('data/deskar_catalog.pdf')
start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = int(sys.argv[2]) if len(sys.argv) > 2 else start + 1

for i in range(start, end):
    p = doc[i]
    pix = p.get_pixmap(matrix=pymupdf.Matrix(2, 2))
    tmp = f'/tmp/ocr_page_{i}.png'
    pix.save(tmp)
    res = ocr.ocr(tmp, cls=False)
    print(f'===== page {i} =====')
    if res and res[0]:
        for line in res[0]:
            box = [[int(x) for x in pt] for pt in line[0]]
            text, conf = line[1]
            xs = [pt[0] for pt in box]; ys = [pt[1] for pt in box]
            print(f'[{min(xs):4d},{min(ys):4d} {max(xs):4d},{max(ys):4d}] {conf:.2f} {text}')