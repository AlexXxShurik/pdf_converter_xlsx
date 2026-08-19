import sys
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks, ocr_rotated_cw
from converter.table_geometry import find_table_headers, parse_legend, ALLOY_RE

PAGE_H = 841.89
doc = open_pdf('data/deskar_catalog.pdf')
i = 41
img2, z2 = render_page(doc, i, 2.0)
blocks = ocr_blocks(img2, z2)
headers = find_table_headers(blocks)
print('find_table_headers ->', headers)
img6, z6 = render_page(doc, i, 6.0)

# manually scan every y band that LOOKS like a header (Moenb/Monenb tokens)
for b in sorted(blocks, key=lambda b: b['cy']):
    t = b['text'].strip()
    if t.lower() in ('moenb', 'monenb', 'moeb', 'модель', 'moenь', 'moeнb', 'monenь'):
        print(f'-- candidate header token {t!r} at y={b["cy"]:.1f} cx={b["cx"]:.1f}')