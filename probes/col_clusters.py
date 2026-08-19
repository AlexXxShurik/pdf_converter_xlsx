import sys
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks

doc = open_pdf('data/AccKee2025.pdf')
i = 3
img4, z4 = render_page(doc, i, 4.0)
blocks = ocr_blocks(img4, z4)

# зоны таблиц по x
zones = [(60, 345), (355, 575), (635, 885), (895, 1130)]
for (x0, x1) in zones:
    toks = [b for b in blocks if 220 <= b['cy'] <= 705 and x0 <= b['cx'] <= x1]
    xs = sorted(t['cx'] for t in toks)
    cols = []
    cur = [xs[0]]
    for x in xs[1:]:
        if x - cur[-1] <= 12:
            cur.append(x)
        else:
            cols.append(sum(cur)/len(cur))
            cur = [x]
    if cur:
        cols.append(sum(cur)/len(cur))
    print(f'--- zone {x0}-{x1}: {len(cols)} column clusters ---')
    for c in cols:
        # значения в этой колонке
        vals = sorted({t['text'] for t in toks if abs(t['cx']-c) <= 7})
        print('  x=%.1f  n=%d  %r' % (c, len(vals), vals[:12]))