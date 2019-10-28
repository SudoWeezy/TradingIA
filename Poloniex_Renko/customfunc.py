from decimal import Decimal

def add_one(v):
    after_comma = Decimal(v).as_tuple()[-1]*-1
    add = Decimal(1) / Decimal(10**after_comma)
    return Decimal(v) + add

def minus_one(v):
    after_comma = Decimal(v).as_tuple()[-1]*-1
    add = Decimal(1) / Decimal(10**after_comma)
    return Decimal(v) - add