import sys
sys.path.insert(0, '.')
from converter.pdf_to_images import open_pdf, render_page
from converter.ocr_engine import ocr_blocks

doc = open_pdf('data/AccKee2025.pdf')
i = int(sys.argv[1]) if len(sys.argv) > 1 else 4
img2, z2 = render_page(doc, i, 2.0)
blocks = ocr_blocks(img2, z2)

W = doc[i].rect.width
H = doc[i].rect.height
nrows = 45
ncols = 64
grid = [[' '] * ncols for _ in range(nrows)]
cell_w = W / ncols
cell_h = H / nrows
for b in blocks:
    t = b['text']
    cx = int(b['cx'] / cell_w)
    cy = int(b['cy'] / cell_h)
    if 0 <= cx < ncols and 0 <= cy < nrows:
        grid[cy][cx] = '#'
print(f'--- page {i} {W:.0f}x{H:.0f} ASCII map (# = text block) ---')
for r in range(nrows):
    print(f'{r*cell_h:5.0f} |{"".join(grid[r])}|')