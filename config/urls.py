from django.contrib import admin
from django.urls import include, path

# The admin site lives at /admin/ and everything else is handled by the invoices app.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("invoices.urls")),
]
