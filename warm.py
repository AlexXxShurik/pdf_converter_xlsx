import pymupdf
from converter.ocr_words import ocr_page
pdf = pymupdf.open('data/AccKee2025.pdf')
for pno in range(0, 84):
    ocr_page(pdf[pno])
print("done")
