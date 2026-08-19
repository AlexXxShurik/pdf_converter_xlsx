from converter.pdf_to_images import render_page
from converter.ocr_engine import ocr_blocks, ocr_rotated_cw
from converter.preprocess import detect_dots
from converter.table_geometry import (
    MODEL_RE, NUMBER_RE,
    find_table_headers, find_model_rows, attribute_columns,
    parse_legend, assign_groups, match_dots_to_alloys,
)

PAGE_W = 595.28
PAGE_H = 841.89


def _crop(img, zoom, x0p, y0p, x1p, y1p):
    x0, x1 = int(x0p * zoom), min(int(x1p * zoom), img.shape[1])
    y0, y1 = int(y0p * zoom), min(int(y1p * zoom), img.shape[0])
    return img[y0:y1, x0:x1], x0p, y0p


def _value_columns(number_blocks, model_x_right, legend_x0, header_y, band_end,
                   tol=13.0):
    """Cluster number-token x-centres into attribute value columns (per table)."""
    xs = [b['cx'] for b in number_blocks
          if model_x_right + 2 < b['cx'] < legend_x0 - 4
          and header_y + 12 < b['cy'] < band_end]
    if not xs:
        return []
    xs.sort()
    cols = []
    cur = [xs[0]]
    for x in xs[1:]:
        if x - cur[-1] <= tol:
            cur.append(x)
        else:
            cols.append(sum(cur) / len(cur))
            cur = [x]
    if cur:
        cols.append(sum(cur) / len(cur))
    return cols


def _label_for_column(column_x, header_labels, tol=14.0):
    best = None
    best_d = tol + 1
    for label, cx in header_labels:
        d = abs(column_x - cx)
        if d < best_d:
            best_d = d
            best = (label, cx)
    return best


def _to_float(text):
    t = text.replace(',', '.').replace(' ', '')
    try:
        return float(t)
    except ValueError:
        return None


def _parse_table(blocks, img2, z2, img6, z6, img3, z3, header_y, band_end):
    if band_end <= header_y:
        band_end = PAGE_H
    model_rows = find_model_rows(blocks, header_y + 5, band_end)
    if not model_rows:
        return []

    model_tokens = [b for b in blocks
                    if header_y + 5 <= b['cy'] <= band_end
                    and MODEL_RE.match(b['text'].strip().upper())]
    model_x_right = max((b['x1'] for b in model_tokens), default=210.0) + 2

    # alloy legend + group labels for this table
    leg_img, leg_x0, leg_y0 = _crop(img6, z6, 360, header_y - 24, 590, header_y + 33)
    leg_blocks = ocr_rotated_cw(leg_img, z6, leg_x0, leg_y0)
    grp_img, grp_x0, grp_y0 = _crop(img6, z6, 360, header_y - 31, 590, header_y - 11)
    grp_blocks = ocr_blocks(grp_img, z6, grp_x0, grp_y0, min_conf=0.4)
    alloys, groups = parse_legend(leg_blocks, grp_blocks)
    if not alloys:
        return []
    group_of = assign_groups(alloys, groups)
    legend_x0 = min(a[1] for a in alloys) - 6
    legend_x1 = max(a[1] for a in alloys) + 6

    # attribute labels from the header band (excluding the legend zone)
    hb_img, hb_x0, hb_y0 = _crop(img6, z6, 95, header_y - 12, legend_x0 - 4, header_y + 16)
    hb = ocr_blocks(hb_img, z6, hb_x0, hb_y0, min_conf=0.3)
    header_labels = attribute_columns(hb, model_x_right)
    label_centers = {label: cx for label, cx in header_labels}

    # value columns from data numbers (between model column and legend)
    number_blocks = [b for b in blocks if NUMBER_RE.match(b['text'].strip())]
    value_cols = _value_columns(number_blocks, model_x_right, legend_x0,
                                header_y, band_end)
    attrs = []
    for cx in value_cols:
        m = _label_for_column(cx, header_labels)
        if m is not None:
            attrs.append((m[0], cx))
    for label, cx in header_labels:
        if all(abs(cx - ac) > 14 for _, ac in attrs):
            attrs.append((label, cx))
    attrs.sort(key=lambda a: a[1])

    # dots (alloy markers) inside this table band
    zone = (legend_x0, header_y + 26, legend_x1, band_end)
    dots = detect_dots(img3, zone)
    dot_alloys = match_dots_to_alloys(dots, alloys)

    products = []
    for row in model_rows:
        ry = row['y']
        attrs_out = {}
        for label, cx in attrs:
            best = None
            best_d = 16.0
            for b in number_blocks:
                if abs(b['cy'] - ry) > 12:
                    continue
                d = abs(b['cx'] - cx)
                if d < best_d:
                    best_d = d
                    best = b
            if best is not None and best_d < 16.0:
                v = _to_float(best['text'])
                if v is not None:
                    attrs_out[label] = v
        alloys_out = []
        for code, dx, dy in dot_alloys:
            if abs(dy - ry) <= 15.0:
                grp = group_of.get(code, '')
                if grp:
                    alloys_out.append((code, grp))
        alloys_out = list(dict.fromkeys(alloys_out))
        for model in row['models']:
            products.append({
                'model': model,
                'attrs': dict(attrs_out),
                'alloys': alloys_out,
            })
    return products


def parse_page(doc, page_index):
    """Parse one page (possibly multiple tables). Returns list of products."""
    img2, z2 = render_page(doc, page_index, 2.0)
    blocks = ocr_blocks(img2, z2)
    headers = find_table_headers(blocks)
    if not headers:
        return []
    img6, z6 = render_page(doc, page_index, 6.0)
    img3, z3 = render_page(doc, page_index, 3.0)
    products = []
    for idx, hy in enumerate(headers):
        band_end = headers[idx + 1] - 20 if idx + 1 < len(headers) else PAGE_H
        products.extend(_parse_table(blocks, img2, z2, img6, z6, img3, z3, hy, band_end))
    return products