import argparse

from converter.pipeline import process_pdf


def main():
    ap = argparse.ArgumentParser(
        description='Извлечение данных из PDF-каталога AccKee в XLSX.')
    ap.add_argument('pdf', default='data/AccKee2025.pdf', nargs='?')
    ap.add_argument('out', default='result.xlsx', nargs='?')
    ap.add_argument('--pages', help='page ranges, 1-based inclusive, e.g. 4-5, 7, 12-13')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()

    pr = None
    if args.pages:
        ranges = []
        for part in args.pages.split(','):
            part = part.strip()
            if '-' in part:
                a, b = part.split('-')
                ranges.append((int(a) - 1, int(b)))
            else:
                p = int(part)
                ranges.append((p - 1, p))
        pr = ranges
    process_pdf(args.pdf, args.out, pr, args.verbose)


if __name__ == '__main__':
    main()