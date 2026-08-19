import sys
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks
from converter.table_geometry import (
    find_table_headers, find_model_rows, MODEL_RE, NUMBER_RE,
)

PAGE_H = 841.89
doc = open_pdf('data/deskar_catalog.pdf')
for i in range(20, 50):
    img2, z2 = render_page(doc, i, 2.0)
    blocks = ocr_blocks(img2, z2)
    headers = find_table_headers(blocks)
    if not headers:
        continue
    for idx, hy in enumerate(headers):
        band_end = headers[idx + 1] - 20 if idx + 1 < len(headers) else PAGE_H
        rows = find_model_rows(blocks, hy + 5, band_end)
        if len(rows) < 2:
            continue
        nums = [b for b in blocks
                if NUMBER_RE.match(b['text'].strip())
                and hy + 5 <= b['cy'] <= band_end
                and 200 < b['cx'] < 370]
        # cluster numbers into columns by x
        xs = sorted(b['cx'] for b in nums)
        cols = []
        cur = [xs[0]]
        for x in xs[1:]:
            if x - cur[-1] <= 13:
                cur.append(x)
            else:
                cols.append(sum(cur) / len(cur)); cur = [x]
        if cur:
            cols.append(sum(cur) / len(cur))
        for cx in cols:
            col_nums = [b for b in nums if abs(b['cx'] - cx) <= 7]
            n = len(col_nums)
            if n < len(rows):
                ys = sorted(b['cy'] for b in col_nums)
                # merged if a gap between consecutive model rows has no value
                gaps = []
                for y in rows:
                    if not any(abs(b['cy'] - y['y']) < 12 for b in col_nums):
                        gaps.append(round(y['y']))
                if gaps:
                    print(f'p{i} hy={hy:.0f} col={cx:.0f} vals={n} rows={len(rows)} '
                          f'missing_rows={gaps} samples={[b["text"] for b in col_nums[:3]]}')