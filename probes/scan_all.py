"""Scan the whole catalog: find pages whose tables have the required headers."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks
from converter.table_geometry import find_table_headers, MODEL_RE

PDF = 'data/deskar_catalog.pdf'


def main():
    doc = open_pdf(PDF)
    out = open('/tmp/scan_all.txt', 'w')
    for i in range(doc.page_count):
        img, z = render_page(doc, i, 2.0)
        blocks = ocr_blocks(img, z)
        headers = find_table_headers(blocks)
        if not headers:
            continue
        models = [b for b in blocks if MODEL_RE.match(b['text'].strip().upper())]
        alloys = [b for b in blocks
                  if b['text'].strip().upper().startswith('LF')
                  and len(b['text'].strip()) >= 5]
        out.write(f'p{i:3d}: headers={[round(h,1) for h in headers]} '
                  f'models={len(models)} alloys={len(alloys)}\n')
        out.flush()
    out.close()


if __name__ == '__main__':
    main()
