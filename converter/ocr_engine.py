import logging

logging.disable(logging.WARNING)

import numpy as np
import cv2

_OCR = None


def get_ocr():
    global _OCR
    if _OCR is None:
        from paddleocr import PaddleOCR
        _OCR = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
    return _OCR


def _norm_block(line, zoom, x0p=0.0, y0p=0.0):
    box = line[0]
    xs = [pt[0] for pt in box]
    ys = [pt[1] for pt in box]
    text, conf = line[1]
    return {
        'text': text,
        'conf': conf,
        'x0': x0p + min(xs) / zoom,
        'y0': y0p + min(ys) / zoom,
        'x1': x0p + max(xs) / zoom,
        'y1': y0p + max(ys) / zoom,
        'cx': x0p + (min(xs) + max(xs)) / 2 / zoom,
        'cy': y0p + (min(ys) + max(ys)) / 2 / zoom,
    }


def ocr_blocks(img, zoom, x0p=0.0, y0p=0.0, min_conf=0.3):
    ocr = get_ocr()
    tmp = '/tmp/_ocr_blk.png'
    cv2.imwrite(tmp, img)
    res = ocr.ocr(tmp, cls=False)
    blocks = []
    if res and res[0]:
        for line in res[0]:
            b = _norm_block(line, zoom, x0p, y0p)
            if b['conf'] >= min_conf:
                blocks.append(b)
    return blocks


def ocr_rotated_cw(img, zoom, x0p, y0p, scale=3, min_conf=0.4):
    """OCR a region with vertical (rotated 90°) text.

    Expects light text on dark background. Rotates the region 90° CW so
    vertical text becomes horizontal, OCRs, and maps blocks back to the
    original (pt) coordinates of the region.
    """
    ocr = get_ocr()
    big = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    rot = cv2.rotate(big, cv2.ROTATE_90_CLOCKWISE)
    tmp = '/tmp/_ocr_rot.png'
    cv2.imwrite(tmp, rot)
    res = ocr.ocr(tmp, cls=False)
    blocks = []
    if res and res[0]:
        for line in res[0]:
            box = line[0]
            xs = [pt[0] for pt in box]
            ys = [pt[1] for pt in box]
            text, conf = line[1]
            if conf < min_conf:
                continue
            # ROTATE_90_CLOCKWISE: src_x = dst_y / scale, src_y = dst_x / scale
            src_x0 = (min(ys) + max(ys)) / 2 / scale
            src_y0 = (min(xs) + max(xs)) / 2 / scale
            blocks.append({
                'text': text,
                'conf': conf,
                'cx': x0p + src_x0 / zoom,
                'cy': y0p + src_y0 / zoom,
            })
    return blocks