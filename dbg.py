from converter.pipeline import process_pdf
from converter.xlsx_writer import group_tables
all_tables = process_pdf('data/AccKee2025.pdf', 'results/result_tmp_5382.xlsx',
                          page_range=[(53,54),(82,83)], verbose=False)
for g in group_tables(all_tables):
    print(f"  лист {g['name']}: {len(g['tables'])} tables, total rows {sum(len(t['rows']) for t in g['tables'])}")
