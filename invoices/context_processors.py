from .models import BusinessProfile


def business(request):
    # The sidebar and invoice header both need the business name, so it's
    # made available to every template instead of passing it from each view.
    return {"business": BusinessProfile.load()}
