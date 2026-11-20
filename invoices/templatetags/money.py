from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def cad(value, places=2):
    """
    Format a number as dollars: 1234.5 -> $1,234.50

    Django's intcomma follows the site's locale, and with en-ca it was
    putting spaces in big numbers on some pages ($5 769) and commas on
    others. This keeps every amount in the app looking the same.
    """
    if value in (None, ""):
        value = 0
    places = int(places)
    return f"${Decimal(value):,.{places}f}"
