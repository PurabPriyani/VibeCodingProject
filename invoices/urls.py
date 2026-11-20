from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("clients/", views.client_list, name="client_list"),
    path("clients/<int:pk>/delete/", views.client_delete, name="client_delete"),

    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/new/", views.invoice_create, name="invoice_create"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("invoices/<int:pk>/edit/", views.invoice_edit, name="invoice_edit"),
    path("invoices/<int:pk>/send/", views.invoice_send, name="invoice_send"),
    path("invoices/<int:pk>/remind/", views.invoice_remind, name="invoice_remind"),
    path("invoices/<int:pk>/status/", views.invoice_status, name="invoice_status"),
    path("invoices/<int:pk>/delete/", views.invoice_delete, name="invoice_delete"),

    path("settings/", views.business_settings, name="settings"),
]
