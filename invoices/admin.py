from django.contrib import admin

from .models import BusinessProfile, Client, Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["number", "client", "issue_date", "due_date", "status", "total"]
    list_filter = ["status"]
    search_fields = ["number", "client__name", "client__company"]
    inlines = [InvoiceItemInline]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "email"]
    search_fields = ["name", "company", "email"]


admin.site.register(BusinessProfile)
