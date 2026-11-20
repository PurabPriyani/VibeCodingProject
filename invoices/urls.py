from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("clients/", views.client_list, name="client_list"),
    path("clients/<int:pk>/delete/", views.client_delete, name="client_delete"),

    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/new/", views.invoice_create, name="invoice_create"),
    path("invoices/<int:pk>/edit/", views.invoice_edit, name="invoice_edit"),

    path("settings/", views.business_settings, name="settings"),
]
