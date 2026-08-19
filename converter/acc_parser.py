"""Гибридный парсер страниц AccKee2025.pdf.

Данные — из текстового слоя (page.get_text('words')), границы колонок и
объединённых ячеек — из векторных линий сетки (page.get_drawings()).

parse_page() возвращает список таблиц:
{
    'x0': float, 'x1': float,
    'columns': [{'label': str|None, 'cx': float, 'x0': float, 'x1': float}, ...],
    'models': [str, ...],                       # модели строк таблицы
    'rows': [ [value, ...], ... ]               # по колонкам columns
}
"""
import re

MODEL_RE = re.compile(
    r"^\d{1,2}[A-Z]{1,3}\d{2,3}(\.\d)?-\d{1,3}[A-Z]{1,4}\d{2,3}(?:/\d{2})?$"
)
KOD_MODEL_RE = re.compile(
    r"^KOD\d{2,3}-[2345]D-S\d{2}(?:/\d{2})?-SO\d{2}$"
)
KCD_MODEL_RE = re.compile(
    r"^KCD\d{3}-[2345]D-S\d{2}(?:/S\d{2})?-WC\d{2}$"
)
KSD_MODEL_RE = re.compile(
    r"^KSD\d{3}-[2345]D-S\d{2}(?:/\d{2})?-SP\d{2}(?:/\d{2})?$"
)
C_MODEL_RE = re.compile(
    r"^C\d{2}-[2345]D\d{2,3}(\.\d)?-\d{2,3}SP\d{2}$"
)
C_NPT_MODEL_RE = re.compile(
    r"^C\d+(?:\.\d+)?-\dD\d{4}$"
)
C6D_MODEL_RE = re.compile(
    r"^C\d{2}-\dD\d{2}-\d{3}WC\d{2}$"
)
PDL_MODEL_RE = re.compile(
    r"^PDL\d{3}D\dS\d{2}$"
)
K2D_MODEL_RE = re.compile(
    r"^K[2345]D\d{5}-\d{2}$"
)
MGU_MODEL_RE = re.compile(
    r"^MGU\d{4}_FC\d{2}_SP\d{2}$"
)
TCAP_MODEL_RE = re.compile(
    r"^TCAP\d{2}[RL]\d(?:\.\d{2})?D$"
)
SP_MODEL_RE = re.compile(r"^SP\d{2,3}$")


def is_model(text):
    """Модель строки таблицы: 2D/3D (SP/SOMT), KOD/KCD/KSD, C, PDL, K2D, MGU."""
    return bool(MODEL_RE.match(text) or KOD_MODEL_RE.match(text)
                or KCD_MODEL_RE.match(text) or KSD_MODEL_RE.match(text)
                or C_MODEL_RE.match(text) or C_NPT_MODEL_RE.match(text)
                or C6D_MODEL_RE.match(text) or PDL_MODEL_RE.match(text)
                or K2D_MODEL_RE.match(text) or MGU_MODEL_RE.match(text)
                or TCAP_MODEL_RE.match(text))
NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?$")


def _words(page):
    out = []
    for x0, y0, x1, y1, text, *_ in page.get_text('words'):
        out.append({'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                    'cx': (x0 + x1) / 2, 'cy': (y0 + y1) / 2, 'text': text})
    return _merge_tcap(out)


TCAP_TOKEN_RE = re.compile(r"^\d{2}[RL]$")
TCAP_D_RE = re.compile(r"^\d(?:\.\d{2})?D$")


def _merge_tcap(words):
    """Склеить токены модели TCAP: 'TCAP' + '08R' + '2.25D' → 'TCAP08R2.25D'.

    На стр. 21 (TCAP-3DN/3D) модель в текстовом слое разбита на 3 отдельных
    токена в одной строке. Объединяем их в один токен (cx = левый край TCAP),
    чтобы is_model() распознал модель и строка таблицы строилась по нему.
    """
    out = []
    i = 0
    while i < len(words):
        w = words[i]
        if w['text'] == 'TCAP':
            j = i + 1
            nn = None
            while j < len(words):
                n = words[j]
                if abs(n['cy'] - w['cy']) > 3:
                    break
                if TCAP_TOKEN_RE.match(n['text']):
                    nn = n
                    break
                j += 1
            if nn is not None:
                k = j + 1
                dd = None
                while k < len(words):
                    d = words[k]
                    if abs(d['cy'] - w['cy']) > 3:
                        break
                    if TCAP_D_RE.match(d['text']):
                        dd = d
                        break
                    k += 1
                if dd is not None:
                    out.append({'x0': w['x0'], 'y0': w['y0'],
                                'x1': dd['x1'], 'y1': dd['y1'],
                                'cx': w['cx'], 'cy': w['cy'],
                                'text': w['text'] + nn['text'] + dd['text']})
                    i = k + 1
                    continue
        out.append(w)
        i += 1
    return out


def _vlines(page, min_len=450.0, y0=190.0, y1=780.0):
    """Вертикальные длинные линии сетки → границы колонок (список x)."""
    xs = set()
    for d in page.get_drawings():
        for it in d['items']:
            if it[0] != 'l':
                continue
            a, b = it[1], it[2]
            if abs(a.x - b.x) > 0.5:
                continue
            ya, yb = sorted((a.y, b.y))
            if yb - ya < min_len:
                continue
            xs.add(round(a.x, 2))
    return sorted(xs)


def _table_vlines(page, x0, x1, data_y0=225.0, bottom=780.0):
    """Вертикальные линии внутри x-диапазона таблицы, пересекающие зону данных.

    Длина >= 15, линия пересекает зону данных (ya < bottom) — границы колонок
    (в т.ч. короткие, как на стр. KOD, где колонки обрываются на нижней рамке
    маленькой таблицы).
    """
    xs = set()
    for d in page.get_drawings():
        for it in d['items']:
            if it[0] != 'l':
                continue
            a, b = it[1], it[2]
            if abs(a.x - b.x) > 0.5:
                continue
            if not (x0 - 5 <= a.x <= x1 + 5):
                continue
            ya, yb = sorted((a.y, b.y))
            if yb - ya < 15:
                continue
            if yb <= data_y0:
                continue
            if ya >= bottom - 1.0:
                continue
            xs.add(round(a.x, 2))
    return sorted(xs)


def _hlines_covering(page, cx, y0=190.0, y1=780.0):
    """Горизонтальные линии сетки, покрывающие x-центр колонки cx."""
    ys = set()
    for d in page.get_drawings():
        for it in d['items']:
            if it[0] != 'l':
                continue
            a, b = it[1], it[2]
            if abs(a.y - b.y) > 0.5:
                continue
            if not (y0 <= a.y <= y1):
                continue
            ax0, ax1 = sorted((a.x, b.x))
            if ax0 <= cx <= ax1:
                ys.add(round(a.y, 2))
    return sorted(ys)


def _find_sp_tables(page):
    """Spare Parts таблицы внизу страницы (x 900-1141, y 747-773).

    Рамки: горизонтальные линии (span>150pt) в зоне y 730-780 — верх/низ.
    Заголовки (type/diameter/.../Wrench) на y≈742-744 выше верхней рамки.
    Значения объединённых колонок (напр. type='SP' на 3 строки) дублируются
    на все строки диапазона.
    """
    words = _words(page)
    draws = page.get_drawings()
    hlines = []
    for d in draws:
        for it in d['items']:
            if it[0] != 'l':
                continue
            a, b = it[1], it[2]
            if abs(a.y - b.y) > 0.5:
                continue
            if not (730 <= a.y <= 780):
                continue
            ax0, ax1 = sorted((a.x, b.x))
            if ax1 - ax0 < 150:
                continue
            hlines.append((round(a.y, 1), round(ax0, 1), round(ax1, 1)))
    hlines.sort()
    result = []
    # группируем линии по x-span: (x0,x1) → все y
    groups = {}
    for y, x0, x1 in hlines:
        groups.setdefault((x0, x1), []).append(y)
    for (x0, x1), ys in groups.items():
        ys = sorted(ys)
        if len(ys) < 2 or ys[-1] - ys[0] >= 60:
            continue
        y0, y1 = ys[0], ys[-1]
        # вертикальные линии внутри зоны данных (между рамками)
        vxs = set()
        for d in draws:
            for it in d['items']:
                if it[0] != 'l':
                    continue
                a, b = it[1], it[2]
                if abs(a.x - b.x) > 0.5:
                    continue
                if not (x0 - 5 <= a.x <= x1 + 5):
                    continue
                ya, yb = sorted((a.y, b.y))
                # линия пересекает зону данных (может выходить за её верх)
                if not (ya < y1 - 2 and yb > y0 + 2):
                    continue
                if yb - ya < 15:
                    continue
                vxs.add(round(a.x, 2))
        bounds = [x0] + sorted(vxs) + [x1]
        cols = []
        for i in range(len(bounds) - 1):
            c0, c1 = bounds[i], bounds[i + 1]
            if c1 - c0 < 3:
                continue
            cols.append({'cx': (c0 + c1) / 2, 'x0': c0, 'x1': c1,
                         'label': None})
        # строки: y-кластеры токенов в зоне данных
        row_words = [w for w in words if x0 <= w['cx'] <= x1
                     and y0 < w['cy'] < y1]
        ys = sorted({round(w['cy'], 0) for w in row_words})
        # кластеризация: соседние cy ближе 4 → одна строка
        clusters = []
        for cy in ys:
            if clusters and cy - clusters[-1] <= 4:
                clusters[-1] = (clusters[-1] + cy) / 2
            else:
                clusters.append(float(cy))
        rows = []
        for cy in clusters:
            vals = []
            for c in cols:
                toks = sorted((w for w in row_words
                               if c['x0'] <= w['cx'] <= c['x1']
                               and abs(w['cy'] - cy) < 5),
                              key=lambda w: (w['cy'], w['cx']))
                vals.append(' '.join(t['text'] for t in toks))
            rows.append(vals)
        # объединения: колонка merged, если токенов < строк диапазона
        for j, c in enumerate(cols):
            cw = [w for w in row_words if c['x0'] <= w['cx'] <= c['x1']]
            n_rows = len(rows)
            merged = len(cw) < n_rows and len(cw) > 0
            if merged:
                text = ' '.join(w['text'] for w in sorted(cw,
                                  key=lambda w: (w['cy'], w['cx'])))
                for r in rows:
                    r[j] = text
        result.append({'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1,
                       'cols': cols, 'models': [], 'rows': rows,
                       'sp': True})
    return result


def _table_hlines(page, x0, x1):
    """Горизонтальные линии-рамки (span>100) в x-диапазоне, y>150.

    Возвращает отсортированные по y границы таблицы (верх/низ и разделители).
    SP-зона (y 730-780) обрабатывается отдельно (_find_sp_tables).
    """
    ys = set()
    for d in page.get_drawings():
        for it in d['items']:
            if it[0] != 'l':
                continue
            a, b = it[1], it[2]
            if abs(a.y - b.y) > 0.5:
                continue
            if a.y <= 150:
                continue
            ax0, ax1 = sorted((a.x, b.x))
            if ax1 - ax0 < 100:
                continue
            if ax0 <= x1 and ax1 >= x0:
                ys.add(round(a.y, 2))
    return sorted(ys)


def _vline_bottom(page, x0, x1, data_y0, last_cy):
    """Нижняя граница колонок по вертикальным линиям, пересекающим зону данных.

    На стр. 21 (TCAP) рамки таблиц нарисованы rect-фигурами, а не линиями —
    горизонтальных линий-рамок нет. Колонки по вертикальным линиям (длина >= 15),
    пересекающим зону данных [data_y0, last_cy]. Возвращает max нижней границы
    таких линий (низ самой длинной колонки = низ таблицы).
    """
    best = 0.0
    for d in page.get_drawings():
        for it in d['items']:
            if it[0] != 'l':
                continue
            a, b = it[1], it[2]
            if abs(a.x - b.x) > 0.5:
                continue
            if not (x0 - 5 <= a.x <= x1 + 5):
                continue
            ya, yb = sorted((a.y, b.y))
            if yb - ya < 15:
                continue
            if ya >= last_cy:
                continue
            if yb <= data_y0:
                continue
            best = max(best, yb)
    return best


def _find_tables(page):
    """Таблицы страницы: границы из горизонтальных линий-«рамок».

    Верхняя рамка таблицы — самая верхняя линия-рамка в её x-диапазоне
    (y может быть ~221.8 или ~187.8 в зависимости от страницы). Нижняя — самая
    нижняя, исключая SP-группы (≥2 близких линий в y 730-780). Колонки =
    интервалы между вертикальными линиями сетки внутри диапазона.
    """
    words = _words(page)
    draws = page.get_drawings()

    hlines = []
    for d in draws:
        for it in d['items']:
            if it[0] != 'l':
                continue
            a, b = it[1], it[2]
            if abs(a.y - b.y) > 0.5:
                continue
            if a.y <= 150:
                continue
            ax0, ax1 = sorted((a.x, b.x))
            if ax1 - ax0 < 100:
                continue
            hlines.append((round(a.x, 1), round(b.x, 1), round(a.y, 1)))

    # SP-группы: ≥2 близких линий в y 730-780 с одинаковым x-span.
    # Исключаются ТОЛЬКО линии, у которых совпадает весь (x0,x1,y),
    # иначе нижние рамки обычных таблиц с той же y-координатой теряются.
    sp_lines = set()
    groups = {}
    for x0, x1, y in hlines:
        if 730 <= y <= 780:
            groups.setdefault((x0, x1), []).append(y)
    for (x0, x1), ys in groups.items():
        ys = sorted(ys)
        if len(ys) >= 2 and ys[-1] - ys[0] < 60:
            for y in ys:
                sp_lines.add((x0, x1, y))

    # кластеры таблиц по левой границе рамки
    hlines.sort()
    clusters = []
    for x0, x1, y in hlines:
        if (x0, x1, y) in sp_lines:
            continue
        for c in clusters:
            if abs(c['x0'] - x0) < 3:
                c['x1'] = max(c['x1'], x1)
                c['ys'].append(y)
                break
        else:
            clusters.append({'x0': x0, 'x1': x1, 'ys': [y]})

    result = []
    for c in clusters:
        ys = sorted(c['ys'])
        if len(ys) < 2:
            continue
        x0, x1 = c['x0'], c['x1']
        # модели в x-диапазоне кластера, отсортированные по y
        models_in = sorted((w for w in words if is_model(w['text'])
                            and x0 <= w['cx'] <= x1 and ys[0] < w['cy']),
                           key=lambda w: w['cy'])
        if not models_in:
            continue
        # блоки моделей: большой разрыв по y (>45) = отдельная таблица
        # (напр. K2D и K3D на стр. 20: шаг строк ~11, разрыв между таблицами
        #  ~268pt; C25-6D и C25-8D на стр. 24: разрыв ~58pt).
        # Внутри таблицы разрывы строк < 40.
        blocks = [[models_in[0]]]
        for m in models_in[1:]:
            if m['cy'] - blocks[-1][-1]['cy'] > 45:
                blocks.append([m])
            else:
                blocks[-1].append(m)
        for block in blocks:
            # границы: линии кластера + полные линии, покрывающие x-диапазон
            # (ложные кластеры из линий-сепараторов объединений, напр. стр. 24
            #  x0=698.6, получают настоящие рамки 646.5-1075.5 → их потом
            #  отсекает фильтр дубликатов в parse_page)
            ys_ext = set(ys)
            for lx0, lx1, ly in hlines:
                if lx0 <= x0 + 1 and lx1 >= x1 - 1:
                    ys_ext.add(ly)
            ys_ext = sorted(ys_ext)
            top = max((y for y in ys_ext if y < block[0]['cy']),
                      default=ys[0])
            # нижняя рамка: линия после последней модели. Если такой линии нет
            # (стр. 21 TCAP — рамки нарисованы rect-фигурами) или она далеко,
            # берём низ вертикальных линий колонок.
            line_cands = [y for y in ys_ext if y > block[-1]['cy'] + 2]
            vbot = _vline_bottom(page, x0, x1, top + 3.0, block[-1]['cy'])
            if line_cands:
                bottom = min(min(line_cands), vbot) if vbot else min(line_cands)
            else:
                bottom = vbot if vbot else ys_ext[-1]
            cols_x = _table_vlines(page, x0, x1, data_y0=top + 3.0,
                                   bottom=bottom)
            bounds = [x0] + cols_x + [x1]
            cols = []
            for i in range(len(bounds) - 1):
                c0, c1 = bounds[i], bounds[i + 1]
                if c1 - c0 < 3:
                    continue
                cols.append({'cx': (c0 + c1) / 2, 'x0': c0, 'x1': c1,
                             'label': None})
            result.append({'x0': x0, 'x1': x1, 'cols': cols,
                           'col_bounds': bounds, 'top': top, 'bottom': bottom})
    return result


def _table_models(table, words):
    """Модели таблицы (Spec-колонка) → отсортированные по y токены."""
    y_lo = table['top'] - 1.0
    models = []
    for w in words:
        if not (table['x0'] <= w['cx'] <= table['x1']):
            continue
        if not (y_lo <= w['cy'] <= table['bottom'] + 1.0):
            continue
        if is_model(w['text']):
            models.append(w)
    models.sort(key=lambda m: (m['cy'], m['cx']))
    return models


def _column_rows(table, page, words):
    """Для каждой колонки определить ячейки (y0, y1, tokens) и признак merged.

    Ячейка = интервал между горизонтальными линиями сетки, покрывающими
    x-центр колонки. Если внутри интервала токенов меньше, чем строк моделей —
    это объединённая ячейка (значение дублируется на все строки интервала).
    Возвращает {cx: {'cells': [...], 'merged': bool}}.
    """
    out = {}
    y_lo = table['top'] - 1.0
    y_hi = table['bottom'] + 1.0
    for c in table['cols']:
        cx = c['cx']
        hs = _hlines_covering(page, cx, y0=y_lo, y1=y_hi)
        col_words = [w for w in words
                     if c['x0'] <= w['cx'] <= c['x1'] and y_lo <= w['cy'] <= y_hi]
        cells = []
        if len(hs) >= 2:
            for i in range(len(hs) - 1):
                y0, y1 = hs[i], hs[i + 1]
                toks = sorted((w for w in col_words if y0 < w['cy'] < y1),
                              key=lambda w: (w['cy'], w['cx']))
                cells.append({'y0': y0, 'y1': y1, 'tokens': toks})
        out[cx] = {'cells': cells, 'col_words': col_words}
    return out


def _join_tokens(tokens):
    """Склеить токены ячейки: '20','/','25' → '20/25'; 'SP..A','SP..B' → 'SP..A SP..B'."""
    parts = [t['text'] for t in tokens]
    if not parts:
        return ''
    s = ' '.join(parts)
    return re.sub(r'\s*/\s*', '/', s)


def parse_page(page):
    """Распознать одну страницу AccKee → список таблиц (dict)."""
    words = _words(page)
    tables = _find_tables(page)
    tables += _find_sp_tables(page)
    result = []
    for t in tables:
        if t.get('sp'):
            # Spare Parts: заголовки из текстового слоя
            from converter.acc_headers import sp_headers
            labels = sp_headers(page, t)
            for c, lab in zip(t['cols'], labels):
                c['label'] = lab
            result.append(t)
            continue
        models = _table_models(t, words)
        if not models:
            continue
        colinfo = _column_rows(t, page, words)

        # строки моделей по y
        row_ys = [m['cy'] for m in models]
        n_rows = len(row_ys)

        # для каждой колонки решить: объединённая или обычная
        for c in t['cols']:
            cx = c['cx']
            info = colinfo[cx]
            # объединённая, если в какой-то ячейке токенов в ≤2 раза меньше
            # строк в ней (значение дублируется на диапазон). Так ловятся и
            # колонки с промежуточными линиями (Ds/l3/AI), и одна ячейка на
            # всю таблицу (T5 Ds='32', T2 AI='SOMT130408').
            # Обычная колонка (напр. kg, 30 токенов на 50 строк, ratio 0.6)
            # критерий НЕ считает объединённой.
            merged = False
            for cell in info['cells']:
                n_in = sum(1 for y in row_ys if cell['y0'] < y < cell['y1'])
                if n_in > 0:
                    k = len(cell['tokens'])
                    if 0 < k < n_in and k * 2 <= n_in:
                        merged = True
                        break
            info['merged'] = merged

        # построить матрицу значений
        rows = []
        for cy in row_ys:
            vals = [None] * len(t['cols'])
            for j, c in enumerate(t['cols']):
                info = colinfo[c['cx']]
                if info['merged']:
                    text = ''
                    for cell in info['cells']:
                        if cell['y0'] < cy < cell['y1']:
                            text = _join_tokens(cell['tokens'])
                            break
                    vals[j] = text
                else:
                    best, best_d = None, 5.0
                    for w in info['col_words']:
                        d = abs(w['cy'] - cy)
                        if d < best_d:
                            best_d, best = d, w
                    vals[j] = best['text'] if best is not None else ''
            rows.append(vals)
        result.append({'x0': t['x0'], 'x1': t['x1'], 'cols': t['cols'],
                       'models': [m['text'] for m in models], 'rows': rows,
                       'top': t['top'], 'bottom': t['bottom']})
    # убрать дубликаты: вложенная таблица (по x и y) с подмножеством моделей
    # другой таблицы (напр. стр. 24: кластер из линий-сепараторов Spec/L/l1/l2
    # даёт вторую таблицу с теми же C25-6D моделями, но 4 колонками вместо 10).
    final = []
    for a in result:
        dup = False
        for b in result:
            if a is b or b.get('sp'):
                continue
            if a.get('sp'):
                continue
            if b['x0'] - 1 <= a['x0'] and a['x1'] <= b['x1'] + 1 \
                    and b['top'] - 1 <= a['top'] and a['bottom'] <= b['bottom'] + 1:
                b_models = set(b.get('models', []))
                if b_models and b_models.issuperset(set(a.get('models', []))):
                    dup = True
                    break
        if not dup:
            final.append(a)
    return final