import sys
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks

doc = open_pdf('data/deskar_catalog.pdf')
seen = {}
for i in range(doc.page_count):
    img2, z2 = render_page(doc, i, 2.0)
    blocks = ocr_blocks(img2, z2)
    for b in blocks:
        t = b['text'].strip()
        if len(t) >= 4 and len(t) <= 8:
            low = t.lower()
            if 'мод' in low or 'moen' in low or 'moe' in low[:3] or 'мo' in low[:2]:
                seen.setdefault(t, []).append((i, round(b['cy'])))
print('=== model-header-like tokens ===')
for t in sorted(seen):
    print(f'{t!r}: {seen[t][:6]} ... total {len(seen[t])}')