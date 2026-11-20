from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def cad(value, places=2):
    """
    Formats an amount as Canadian dollars, with a comma between thousands and
    a fixed number of decimal places (two by default, or 0 for whole dollars).

    Django's built-in intcomma follows the site's locale, and with en-ca some
    amounts came out with spaces as the thousands separator. Using one filter
    everywhere keeps amounts looking the same on every page.
    """
    if value in (None, ""):
        value = 0
    places = int(places)
    return f"${Decimal(value):,.{places}f}"
