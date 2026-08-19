"""Заголовки колонок AccKee: OCR узкой полосы шапки по каждой колонке.

Заголовки в текстовом слое отсутствуют (только в растре). OCR кропа y≈196–214
по x-интервалу колонки даёт надёжные метки: Dc, Ds, Specification/Item, Store,
L, l1, l2, l3, Applicable Insert, kg.

Spare Parts: заголовки есть в текстовом слое (y≈742-744) — читаются оттуда.
"""
import cv2
import pymupdf

from converter.ocr_engine import get_ocr

# Нормализация OCR-меток к каноническим
LABEL_FIX = {
    'dc': 'Dc', 'ds': 'Ds', 'specification/item': 'Specification/Item',
    'specification': 'Specification/Item', 'item': 'Specification/Item',
    'store': 'Store', 'applicable insert': 'Applicable Insert',
    'insert': 'Applicable Insert', 'kg': 'kg',
    'l1': 'l1', 'l2': 'l2', 'l3': 'l3', 'l': 'L',
    'q2': 'l2', 'q3': 'l3', "l'": 'l1', '1': 'l1', '2': 'l2', '3': 'l3',
}


def normalize_label(raw):
    key = raw.strip().strip('.').strip().lower().replace(' ', ' ')
    key = ' '.join(key.split())
    return LABEL_FIX.get(key, raw.strip())


def ocr_headers(page, table, zoom=4.0):
    """OCR шапки для каждой колонки таблицы. Возвращает список меток.

    Полоса шапки — зона (top-45, top-5) над верхней рамкой таблицы. Рамка может
    быть на y≈221.8 (обычные страницы) или y≈187.8 (WC-страницы) → полоса
    вычисляется относительно table['top']. Широкая полоса нужна, т.к. субиндексы
    l1/l2/l3 (цифры 1/2/3) лежат ниже самих букв.
    """
    top = table.get('top', 221.8)
    y0, y1 = top - 45.0, top - 5.0
    ocr = get_ocr()
    labels = []
    for c in table['cols']:
        clip = pymupdf.Rect(c['x0'], y0, c['x1'], y1)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
        fn = '/tmp/_acc_hdr.png'
        pix.save(fn)
        res = ocr.ocr(fn, cls=False)
        toks = []
        if res and res[0]:
            for line in res[0]:
                text = line[1][0]
                toks.append(text)
        if toks:
            # берём первый токен (в кропе колонки шапка одна)
            labels.append(normalize_label(toks[0]))
        else:
            labels.append('')
    return labels


def sp_headers(page, table):
    """Заголовки Spare Parts из текстового слоя (полоса над верхней рамкой).

    Рамка может быть на y≈747.6 (стр. 4) или y≈738.7 (стр. 5) → полоса
    (y0-25, y0) над верхней рамкой таблицы.
    Колонки группируются под метками по границам между соседними метками.
    Возвращает список меток по колонкам (для группы Screw метка повторяется).
    """
    y0 = table.get('y0', 747.6)
    words = []
    for w in page.get_text('words'):
        if y0 - 25 <= w[3] <= y0 and table['x0'] <= w[0] <= table['x1']:
            words.append({'x0': w[0], 'x1': w[2], 'cx': (w[0] + w[2]) / 2,
                          'cy': w[3], 'text': w[4]})
    if not words:
        return ['' for _ in table['cols']]
    # склейка 'Blade'+'model' → 'Blade model'
    words.sort(key=lambda w: w['cx'])
    merged = []
    for w in words:
        if merged and merged[-1]['cy'] - w['cy'] < 1.5 \
                and w['cx'] - merged[-1]['x1'] < 15:
            merged[-1]['text'] = merged[-1]['text'] + ' ' + w['text']
            merged[-1]['x1'] = w['x1']
        else:
            merged.append(w)
    # метки как (cx, text) с границами между соседними
    anchors = [(w['cx'], w['text']) for w in merged]
    anchors.sort()
    labels = []
    for c in table['cols']:
        # ищем метку, чей cx ближе всех к центру колонки
        best, best_d = None, 1e9
        for cx, text in anchors:
            d = abs(cx - c['cx'])
            if d < best_d:
                best_d, best = d, (cx, text)
        # колонка принадлежит метке, если ближе чем к соседней метке
        assigned = None
        for i, (cx, text) in enumerate(anchors):
            lo = (anchors[i - 1][0] + cx) / 2 if i > 0 else -1e9
            hi = (cx + anchors[i + 1][0]) / 2 if i < len(anchors) - 1 else 1e9
            if lo <= c['cx'] <= hi:
                assigned = text
                break
        labels.append(assigned if assigned is not None
                      else (best[1] if best else ''))
    return labels