import re

NOISE = re.compile(r'^ЕСЛИ|^ПРИМЕЧАНИЕ|^ВНИМАНИЕ|^ИЗГОТОВЛ', re.IGNORECASE)


def validate_product(p):
    """Drop products that are clearly noise / missing required fields."""
    if not p.get('model') or not p.get('alloys'):
        return False
    if NOISE.match(p['model']):
        return False
    if re.fullmatch(r'LF\d{3,4}', p['model']):
        return False
    return True


def merge_products(products):
    """Dedup by (model, alloy). Returns {key: product}."""
    out = {}
    for p in products:
        if not validate_product(p):
            continue
        for code, group in p['alloys']:
            key = (p['model'], code)
            if key not in out:
                out[key] = {
                    'model': p['model'],
                    'attrs': dict(p['attrs']),
                    'alloys': [(code, group)],
                }
    return out