"""Survey page structure across the catalog to find layout variations."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks
from converter.table_geometry import find_header_y, find_model_rows

PDF = 'data/deskar_catalog.pdf'
pages = [int(x) - 1 for x in sys.argv[1:]] or list(range(0, 252, 10))


def main():
    doc = open_pdf(PDF)
    for i in pages:
        img, z = render_page(doc, i, 2.0)
        blocks = ocr_blocks(img, z)
        hy = find_header_y(blocks)
        models = find_model_rows(blocks, hy) if hy is not None else []
        groups = sorted({b['text'].strip().upper() for b in blocks
                         if hy and abs(b['cy'] - hy) < 35 and 400 <= b['cx'] <= 560
                         and b['text'].strip().upper() in ('P', 'M', 'K')})
        print(f"p{i:3d}: header_y={hy and round(hy, 1)} models={len(models)} groups={groups}")


if __name__ == '__main__':
    main()