import cv2
import numpy as np


def to_gray(img):
    if len(img.shape) == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def upscale(img, factor, interp=cv2.INTER_CUBIC):
    return cv2.resize(img, None, fx=factor, fy=factor, interpolation=interp)


def binarize_light_on_dark(img, threshold=140):
    """Light text on dark background -> white text on black."""
    gray = to_gray(img)
    return (gray > threshold).astype(np.uint8) * 255


def detect_dots(img, zone, min_r=2.0, max_r=5.5):
    """Detect small round dots (alloy markers) inside zone (pt coords).

    zone: (x0, y0, x1, y1) in pt. Returns list of (cx_pt, cy_pt, r_pt).
    """
    x0, y0, x1, y1 = zone
    zoom = img.shape[1] / 595.28  # approximate zoom from image width
    px0, py0, px1, py1 = (int(x0 * zoom), int(y0 * zoom),
                          int(min(x1, 595.28) * zoom), int(min(y1, 841.89) * zoom))
    sub = img[py0:py1, px0:px1]
    if sub.size == 0:
        return []
    gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV, 31, 5)
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    dots = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 4:
            continue
        (cx, cy), r = cv2.minEnclosingCircle(cnt)
        ca = np.pi * r * r
        if ca <= 0:
            continue
        fill = area / ca
        if fill < 0.25 or fill > 1.1:
            continue
        if not (min_r * zoom <= r <= max_r * zoom):
            continue
        dots.append((x0 + cx / zoom, y0 + cy / zoom, r / zoom))
    return dots


def columns_from_projection(band_bright, x0_pt, zoom, min_width_px=8, thr_frac=0.2):
    """Find vertical-text column x-ranges in a bright-on-dark band."""
    colsum = band_bright.sum(axis=0)
    thr = colsum.max() * thr_frac
    cols = []
    in_col = False
    start = 0
    for i in range(len(colsum)):
        if colsum[i] > thr and not in_col:
            in_col = True
            start = i
        elif colsum[i] <= thr and in_col:
            in_col = False
            if i - start >= min_width_px:
                cols.append((start, i))
    if in_col and len(colsum) - start >= min_width_px:
        cols.append((start, len(colsum)))
    return [((a + b) / 2.0 / zoom + x0_pt, a / zoom + x0_pt, b / zoom + x0_pt) for a, b in cols]