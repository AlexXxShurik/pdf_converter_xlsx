import sys
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks, ocr_rotated_cw
from converter.table_geometry import (
    find_table_headers, find_model_rows, MODEL_RE,
    attribute_columns, parse_legend, assign_groups,
)
from converter.parser import _crop, _value_columns, _label_for_column

PAGE_H = 841.89
doc = open_pdf('data/deskar_catalog.pdf')
i = 41
img2, z2 = render_page(doc, i, 2.0)
blocks = ocr_blocks(img2, z2)
headers = find_table_headers(blocks)
print('headers:', headers)
hy = headers[0]
band_end = headers[1] - 20
print('band_end:', band_end)

model_rows = find_model_rows(blocks, hy + 5, band_end)
print('model_rows:', len(model_rows))
model_tokens = [b for b in blocks if hy+5 <= b['cy'] <= band_end and MODEL_RE.match(b['text'].strip().upper())]
model_x_right = max((b['x1'] for b in model_tokens), default=210.0) + 2
print('model_x_right:', model_x_right)

img6, z6 = render_page(doc, i, 6.0)
leg_img, leg_x0, leg_y0 = _crop(img6, z6, 360, hy-24, 590, hy+33)
leg_blocks = ocr_rotated_cw(leg_img, z6, 360, hy-24)
print('legend blocks:')
for b in leg_blocks: print('  ', b['text'], round(b['cx'],1), round(b['cy'],1))
grp_img, grp_x0, grp_y0 = _crop(img6, z6, 360, hy-31, 590, hy-11)
grp_blocks = ocr_blocks(grp_img, z6, 360, hy-31, min_conf=0.4)
print('group blocks:')
for b in grp_blocks: print('  ', b['text'], round(b['cx'],1))
alloys, groups = parse_legend(leg_blocks, grp_blocks)
legend_x0 = min(a[1] for a in alloys) - 6 if alloys else 590
print('legend_x0:', legend_x0)

hb_img, hb_x0, hb_y0 = _crop(img6, z6, 95, hy-12, legend_x0-4, hy+16)
hb = ocr_blocks(hb_img, z6, 95, hy-12, min_conf=0.3)
print('header band blocks:')
for b in sorted(hb, key=lambda b: b['cx']): print('  ', repr(b['text']), round(b['cx'],1), round(b['cy'],1))
header_labels = attribute_columns(hb, model_x_right)
print('header_labels:', header_labels)

number_blocks = [b for b in blocks if b['text'].strip() and (b['text'].strip()[0].isdigit() or b['text'].strip()[0] in '.,') and hy+5 <= b['cy'] <= band_end]
from converter.table_geometry import NUMBER_RE
number_blocks = [b for b in blocks if NUMBER_RE.match(b['text'].strip()) and hy+5 <= b['cy'] <= band_end]
value_cols = _value_columns(number_blocks, model_x_right, legend_x0, hy, band_end)
print('value_cols:', value_cols)
for cx in value_cols:
    print('  col', round(cx,1), '->', _label_for_column(cx, header_labels))