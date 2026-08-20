import fitz
pdf = fitz.open('data/AccKee2025.pdf')
page = pdf[30]
# тип рисования объектов в зоне x 60-560, y 150-780
cnt = {}
segs = []
for d in page.get_drawings():
    kind = d['type']
    cnt[kind] = cnt.get(kind, 0) + 1
    for it in d['items']:
        if it[0] != 'l':
            continue
        a, b = it[1], it[2]
        if 60 <= a.x <= 560 and 150 <= a.y <= 780:
            segs.append((round(a.x,1), round(a.y,1), round(b.x,1), round(b.y,1)))
print("drawing types:", cnt)
print("n segs in SEM zone:", len(segs))
# вертикальные и горизонтальные сегменты в зоне
hs = [(a.x,b.x,a.y) for a.x,a.y,b.x,b.y in segs if abs(a.y-b.y)<=0.5 and abs(a.x-b.x)>=20]
vs = [(a.x,a.y,b.y) for a.x,a.y,b.x,b.y in segs if abs(a.x-b.x)<=0.5 and abs(a.y-b.y)>=10]
print("h in zone:", sorted(set(hs))[:30])
print("v in zone:", sorted(set(vs))[:20])
# покажем прямоугольники
rects = []
for d in page.get_drawings():
    for it in d['items']:
        if it[0] != 're':
            continue
        r = it[1]
        if 60 <= r.x0 <= 560 and 150 <= r.y0 <= 780:
            rects.append((round(r.x0,1), round(r.y0,1), round(r.x1,1), round(r.y1,1)))
print("rects in zone:", sorted(set(rects))[:20], "... n=", len(rects))
