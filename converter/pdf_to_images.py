import pymupdf
import numpy as np


def open_pdf(path):
    return pymupdf.open(path)


def render_page(doc, page_index, zoom):
    page = doc[page_index]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = img[:, :, :3]
    else:
        img = img[:, :, :3].copy()
    return img, zoom