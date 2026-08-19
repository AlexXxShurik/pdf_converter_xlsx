import sys
sys.path.insert(0, '.')

from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks
from converter.table_geometry import (
    find_table_headers, find_model_rows, MODEL_RE, parse_legend,
)

PAGE_H = 841.89

doc = open_pdf('data/deskar_catalog.pdf')
i = 21
img2, z2 = render_page(doc, i, 2.0)
blocks = ocr_blocks(img2, z2)
headers = find_table_headers(blocks)
img6, z6 = render_page(doc, i, 6.0)

for hy in headers:
    leg_img, leg_x0, leg_y0 = (lambda a, b, c, d, e, f:
        (lambda x: (x[0], x[1], x[2]))((
            lambda im: (im, c, e))(img6[int(e*z6):int(f*z6), int(c*z6):int(d*z6)])
        ))(0,0,360,590,hy-24,hy+33)
    from converter.ocr_engine import ocr_rotated_cw
    leg_blocks = ocr_rotated_cw(leg_img, z6, 360, hy-24)
    from converter.table_geometry import ALLOY_RE
    alloys = sorted([(b['text'], b['cx'], b['conf']) for b in leg_blocks
                     if ALLOY_RE.match(b['text'].strip().upper())], key=lambda a: a[1])
    legend_x0 = min(a[1] for a in alloys) - 6 if alloys else 590
    print(f'header_y={hy} legend_x0={legend_x0} alloys={[a[0] for a in alloys]}')
    hb_img, hb_x0, hb_y0 = (lambda a,b,c,d,e,f: (img6[int(e*z6):int(f*z6), int(a*z6):int(b*z6)], a, e))(
        95, legend_x0-4, 0,0, hy-12, hy+16)
    hb = ocr_blocks(hb_img, z6, 95, hy-12, min_conf=0.3)
    for b in sorted(hb, key=lambda b: b['cx']):
        print(f'  hdr {b["text"]!r} cx={b["cx"]:.1f}')