import sys
sys.path.insert(0, '.')

from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks
from converter.table_geometry import (
    find_table_headers, find_model_rows, MODEL_RE,
    attribute_columns, parse_legend, assign_groups,
)

doc = open_pdf('data/deskar_catalog.pdf')
i = 21
img2, z2 = render_page(doc, i, 2.0)
blocks = ocr_blocks(img2, z2)
headers = find_table_headers(blocks)
print('headers:', headers)
for hy in headers:
    print(f'=== header y={hy} ===')
    model_rows = find_model_rows(blocks, hy + 5, headers[headers.index(hy)+1]-20 if headers.index(hy)+1 < len(headers) else 841.89)
    print('model rows:', len(model_rows))
    # header band OCR
    hb = [b for b in blocks if hy - 15 < b['cy'] < hy + 18 and 95 < b['cx'] < 560]
    for b in sorted(hb, key=lambda b: b['cx']):
        print(f'  hdr {b["text"]!r} cx={b["cx"]:.1f}')
    # value numbers in band
    nums = [b for b in blocks if hy + 20 < b['cy'] and b['cx'] > 230 and b['cx'] < 560]
    for b in sorted(nums, key=lambda b: (b['cy'], b['cx']))[:30]:
        print(f'  num {b["text"]!r} cx={b["cx"]:.1f} cy={b["cy"]:.1f}')