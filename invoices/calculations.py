"""
All the money maths lives here so it's in one place and easy to test.

Decimal is used instead of float on purpose: 0.1 + 0.2 in float gives
0.30000000000000004, which is not something you want on an invoice.
"""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def money(value):
    """Round to the nearest cent, the way a cashier would (2.345 -> 2.35)."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def invoice_totals(rows, tax_rate):
    """
    rows is a list of (quantity, unit_price) pairs.
    Returns (subtotal, tax, total).

    Tax is worked out once on the subtotal, not on every line. Taxing each
    line and adding them up can leave the total a cent off.
    """
    subtotal = Decimal("0")
    for quantity, price in rows:
        subtotal += money(Decimal(quantity) * Decimal(price))

    tax = money(subtotal * Decimal(tax_rate) / 100)
    total = subtotal + tax
    return subtotal, tax, total
