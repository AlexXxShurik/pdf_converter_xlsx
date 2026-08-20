"""OCR-источник токенов страницы (визуальное зрение).

Рендерим страницу в изображение, прогоняем PaddleOCR, получаем блоки-токены
с координатами в pt. Это основной источник значений для ВСЕХ страниц каталога
(в т.ч. стр. 52-83, где таблицы нарисованы без текстового слоя).

Текстовый слой (page.get_text('words')) используется отдельно — как корректор
ошибок OCR (D→0, l→1, O→0 и т.п.): где есть точный текстовый токен в ячейке,
берём его, иначе — OCR-блок.

Кэш на диске: results/cache_ocr/p{N}.json — повторные прогоны не рендерят и
не OCR-ят страницы заново.
"""
import json
import os

import cv2
import numpy as np
import pymupdf

from converter.pdf_to_images import render_page
from converter.ocr_engine import get_ocr

_CACHE_DIR = 'results/cache_ocr'


def _norm_line(line, zoom):
    box = line[0]
    xs = [pt[0] for pt in box]
    ys = [pt[1] for pt in box]
    text, conf = line[1]
    return {
        'text': text,
        'conf': conf,
        'x0': min(xs) / zoom,
        'y0': min(ys) / zoom,
        'x1': max(xs) / zoom,
        'y1': max(ys) / zoom,
        'cx': (min(xs) + max(xs)) / 2 / zoom,
        'cy': (min(ys) + max(ys)) / 2 / zoom,
    }


def ocr_page(page, zoom=4, min_conf=0.3, use_cache=True):
    """OCR полной страницы → список токенов {text, conf, cx, cy, x0..y1}."""
    key = page.number if hasattr(page, 'number') else None
    if use_cache and key is not None:
        path = os.path.join(_CACHE_DIR, f'p{key}.json')
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = img[:, :, :3]
    else:
        img = img[:, :, :3].copy()
    ocr = get_ocr()
    tmp = '/tmp/_ocr_page.png'
    cv2.imwrite(tmp, img)
    res = ocr.ocr(tmp, cls=False)
    blocks = []
    if res and res[0]:
        for line in res[0]:
            b = _norm_line(line, zoom)
            if b['conf'] >= min_conf:
                blocks.append(b)
    if use_cache and key is not None:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with open(os.path.join(_CACHE_DIR, f'p{key}.json'), 'w') as f:
            json.dump(blocks, f)
    return blocks