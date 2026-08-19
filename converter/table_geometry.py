import re

MODEL_RE = re.compile(
    r"^[A-Z]{3,5}[0-9]{2}(?:[A-Z][0-9]{3,4}|[0-9]{4,6})[A-Z]?(?:[-/][A-Z0-9-]{1,6})?$"
)
ALLOY_RE = re.compile(r"^LF\d{3,4}$")
NUMBER_RE = re.compile(r"^\d+(?:[.,]\d+)?$")

MODEL_HEADER_RE = re.compile(
    r"^(?:Мо[деа]ль|М[оo][дd][еа]ль|Model|Moe[a-zа-я0-9]{0,5}|Mon[a-zа-я0-9]{0,5})$",
    re.IGNORECASE,
)

# common OCR misreads of attribute header labels (multi-char tokens only);
# keys are alnum-lowercased
LABEL_FIX = {
    'ic': 'I.C', 'lc': 'I.C', 'sic': 'I.C', 'slc': 'I.C',
    'dd': 'd', 'pd': 'd', 'id': 'd', 'di': 'd', '1d': 'd', '0d': 'd',
    'bd': 'd', 'ed': 'd', 'gd': 'd', 'qd': 'd', 'cd': 'd', 'td': 'd',
    'rd': 'd', 'ri': 'd', 'rn': 'd',
    'rr': 'r', 'ir': 'r', 'tr': 'r', 'ri': 'r', 're': 'r',
    'od': 'OD', 'ap': 'ap', 'f': 'f', 'h': 'h', 'b': 'b',
}
_LABEL_ALNUM = str.maketrans('', '', ' .,-!/\\|')


def fix_label(raw):
    t = raw.strip()
    if t in ('L', 'l'):
        return 'L'
    if t in ('S', 's'):
        return 'S'
    if t in ('D', 'd', 'R', 'r'):
        return t
    key = t.translate(_LABEL_ALNUM).lower()
    # single letter after stripping punctuation/space (e.g. ' d', 'B d' -> 'd')
    if len(key) == 1:
        return key.upper() if key in ('D', 'R') else key
    return LABEL_FIX.get(key, t)


def find_table_headers(blocks):
    """Return y-centres of all table header rows on the page.

    Primary signal: the 'Модель'/'Moenb' header token (reliably OCR'd).
    Fallback: rows with >=2 short attribute labels.
    """
    ys = [b['cy'] for b in blocks
          if b['cx'] < 200 and MODEL_HEADER_RE.match(b['text'].strip())]
    if not ys:
        short = [b for b in blocks
                 if 100 < b['cy'] < 850 and 220 <= b['cx'] <= 470
                 and 1 <= len(b['text'].strip()) <= 3]
        short.sort(key=lambda b: b['cy'])
        rows = []
        for b in short:
            if rows and b['cy'] - rows[-1]['y'] <= 12:
                rows[-1]['blocks'].append(b)
            else:
                rows.append({'y': b['cy'], 'blocks': [b]})
        ys = [r['y'] for r in rows if len(r['blocks']) >= 2]
    ys.sort()
    out = []
    for y in ys:
        if out and y - out[-1] <= 20:
            out[-1] = (out[-1] + y) / 2
        else:
            out.append(y)
    return out


def find_model_rows(blocks, y0, y1, max_x=430.0, tol=15.0):
    """Return rows (dicts) with model tokens within the y-band [y0, y1]."""
    models = []
    for b in blocks:
        if b['cx'] > max_x or not (y0 <= b['cy'] <= y1):
            continue
        t = b['text'].strip().upper()
        if MODEL_RE.match(t):
            models.append((b['cy'], t))
    models.sort()
    rows = []
    for cy, t in models:
        if rows and abs(cy - rows[-1]['y']) <= tol:
            rows[-1]['models'].append(t)
        else:
            rows.append({'y': cy, 'models': [t]})
    return rows


def attribute_columns(header_blocks, model_x_right, min_x=130.0, max_x=520.0):
    """From header band OCR tokens, return list of (label, x_center)."""
    cols = []
    for b in header_blocks:
        t = b['text'].strip()
        if not t or b['cx'] < min_x or b['cx'] > max_x:
            continue
        if b['cx'] <= model_x_right + 5:
            continue  # model column
        label = fix_label(t)
        if len(label) > 4 or not re.match(r'^[A-Za-z0-9.]+$', label):
            continue
        cols.append((label, b['cx']))
    cols.sort(key=lambda c: c[1])
    out = []
    for label, cx in cols:
        if out and abs(out[-1][1] - cx) < 6:
            continue
        out.append((label, cx))
    return out


def parse_legend(legend_blocks, group_blocks):
    """Returns (alloys, groups) where alloys = [(code, x_center, conf)]
    and groups = [(letter, x_center)]. Both sorted by x."""
    alloys = []
    for b in legend_blocks:
        t = b['text'].strip().upper()
        if not ALLOY_RE.match(t):
            continue
        alloys.append((t, b['cx'], b['conf']))
    alloys.sort(key=lambda a: a[1])
    groups = []
    for b in group_blocks:
        t = b['text'].strip().upper()
        if t in ('P', 'M', 'K') and len(t) == 1:
            groups.append((t, b['cx']))
    groups.sort(key=lambda g: g[1])
    return alloys, groups


def assign_groups(alloys, groups):
    """Assign each alloy to the nearest group label by x. Returns dict code->group."""
    result = {}
    if not groups:
        return result
    for code, x, conf in alloys:
        nearest = min(groups, key=lambda g: abs(g[1] - x))
        result[code] = nearest[0]
    return result


def match_dots_to_alloys(dots, alloys, x_tol=5.0):
    """Map each dot x to the nearest alloy code within x_tol."""
    res = []
    for dx, dy, r in dots:
        best = None
        best_d = x_tol + 1
        for code, x, conf in alloys:
            d = abs(dx - x)
            if d < best_d:
                best_d = d
                best = code
        if best is not None:
            res.append((best, dx, dy))
    return res