import sys
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks
from converter.table_geometry import (
    find_table_headers, find_model_rows, NUMBER_RE,
)

PAGE_H = 841.89
doc = open_pdf('data/deskar_catalog.pdf')
found = 0
for i in range(20, 50):
    img2, z2 = render_page(doc, i, 2.0)
    blocks = ocr_blocks(img2, z2)
    headers = find_table_headers(blocks)
    if not headers:
        continue
    for idx, hy in enumerate(headers):
        band_end = headers[idx + 1] - 20 if idx + 1 < len(headers) else PAGE_H
        rows = find_model_rows(blocks, hy + 5, band_end)
        if len(rows) < 3:
            continue
        nums = [b for b in blocks
                if NUMBER_RE.match(b['text'].strip())
                and hy + 20 <= b['cy'] <= band_end
                and 230 < b['cx'] < 380]
        # group nums into columns
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
        # value mid-way between two rows => merged cell
        for cx in cols:
            col_nums = [b for b in nums if abs(b['cx'] - cx) <= 8]
            for b in col_nums:
                for a, c in zip(rows, rows[1:]):
                    mid = (a['y'] + c['y']) / 2
                    if abs(b['cy'] - mid) < 4 and (c['y'] - a['y']) < 30:
                        print(f'p{i} hy={hy:.0f} MERGED col={cx:.0f} '
                              f'val={b["text"]!r} cy={b["cy"]:.0f} rows=({a["y"]:.0f},{c["y"]:.0f}) mid={mid:.0f}')
                        found += 1
                        break
print('total merged candidates:', found)