"""Обвязка AccKee: PDF → список таблиц → мультилистовой XLSX."""
import sys

from converter.pdf_to_images import open_pdf
from converter.acc_parser import parse_page
from converter.acc_headers import ocr_headers
from converter.xlsx_writer import write_xlsx


def _label_tables(page, tables):
    """Проставить заголовки колонок (OCR для сверлильных, текст для SP)."""
    for t in tables:
        if t.get('sp'):
            continue  # метки уже проставлены в parse_page
        if t.get('_dim'):
            continue  # справочная таблица размеров: метки заданы вручную
        labels = ocr_headers(page, t)
        for c, lab in zip(t['cols'], labels):
            c['label'] = lab
    return tables


def process_pdf(pdf_path, out_path, page_range=None, verbose=False, on_page=None):
    """Run the whole pipeline: PDF -> result.xlsx.

    page_range: list of (start, stop) 0-based half-open. None = all pages.
    on_page: optional callback(i, page_index, n_tables, total_tables).
    """
    doc = open_pdf(pdf_path)
    if page_range:
        pages = [p for a, b in page_range for p in range(a, b)]
    else:
        pages = range(doc.page_count)

    all_tables = []
    for i in pages:
        try:
            tables = parse_page(doc[i])
            _label_tables(doc[i], tables)
        except Exception as e:  # noqa: BLE001
            if verbose:
                print(f'page {i}: error: {e}', file=sys.stderr, flush=True)
            continue
        all_tables.extend(tables)
        if verbose:
            print(f'page {i}: {len(tables)} tables, total {len(all_tables)}', flush=True)
        if on_page:
            on_page(i, len(tables), len(all_tables))
    write_xlsx(all_tables, out_path)
    return all_tables