from django.contrib import messages
from django.db import transaction
from django.db.models import Count, ProtectedError, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BusinessProfileForm, ClientForm, InvoiceForm, ItemFormSet
from .models import BusinessProfile, Client, Invoice


def dashboard(request):
    return render(request, "invoices/dashboard.html")


# ---------- Clients ----------

def client_list(request):
    form = ClientForm()
    open_modal = False

    if request.method == "POST":
        # The same modal is used for adding and editing. If a client id is
        # sent along, we're editing that client.
        client_id = request.POST.get("client_id")
        if client_id:
            client = get_object_or_404(Client, pk=client_id)
        else:
            client = None

        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            saved = form.save()
            if client:
                messages.success(request, f"{saved} updated")
            else:
                messages.success(request, f"{saved} added")
            return redirect("client_list")

        # Something was wrong, so show the modal again with the errors.
        open_modal = True

    clients = Client.objects.annotate(
        invoice_count=Count("invoices"),
        balance=Sum("invoices__total", filter=Q(invoices__status=Invoice.SENT)),
    )

    return render(request, "invoices/clients.html", {
        "clients": clients,
        "form": form,
        "open_modal": open_modal,
        "editing_id": request.POST.get("client_id", ""),
    })


@require_POST
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    try:
        client.delete()
        messages.success(request, f"{client} deleted")
    except ProtectedError:
        # Deleting a client would wipe out their invoice history, which a
        # business needs to keep for its records.
        messages.error(request, f"{client} has invoices, so they can't be deleted")
    return redirect("client_list")


# ---------- Invoices ----------

def invoice_list(request):
    today = timezone.localdate()
    current = request.GET.get("status", "all")

    invoices = Invoice.objects.select_related("client")
    if current == "draft":
        invoices = invoices.filter(status=Invoice.DRAFT)
    elif current == "sent":
        invoices = invoices.filter(status=Invoice.SENT, due_date__gte=today)
    elif current == "overdue":
        invoices = invoices.filter(status=Invoice.SENT, due_date__lt=today)
    elif current == "paid":
        invoices = invoices.filter(status=Invoice.PAID)

    tabs = [
        ("all", "All"),
        ("draft", "Drafts"),
        ("sent", "Awaiting payment"),
        ("overdue", "Overdue"),
        ("paid", "Paid"),
    ]

    return render(request, "invoices/invoice_list.html", {
        "invoices": invoices,
        "tabs": tabs,
        "current": current,
    })


def invoice_create(request):
    return _invoice_form(request, Invoice())


def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return _invoice_form(request, invoice)


def _invoice_form(request, invoice):
    """Shared by create and edit, since both pages look exactly the same."""
    business = BusinessProfile.load()
    is_new = invoice.pk is None

    form = InvoiceForm(request.POST or None, instance=invoice)
    formset = ItemFormSet(request.POST or None, instance=invoice, prefix="items")

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        # Either the invoice and all its items save, or nothing does.
        with transaction.atomic():
            invoice = form.save()
            formset.instance = invoice
            formset.save()
            invoice.recalculate(business)

        if is_new:
            messages.success(request, f"{invoice.number} created")
        else:
            messages.success(request, f"{invoice.number} updated")
        return redirect("invoice_list")

    if business.charge_tax:
        tax_rate = business.tax_rate
    else:
        tax_rate = 0

    return render(request, "invoices/invoice_form.html", {
        "form": form,
        "formset": formset,
        "invoice": invoice,
        "is_new": is_new,
        "tax_rate": tax_rate,
        "has_clients": Client.objects.exists(),
    })


# ---------- Settings ----------

def business_settings(request):
    profile = BusinessProfile.load()
    form = BusinessProfileForm(request.POST or None, instance=profile)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Business details saved")
        return redirect("settings")

    return render(request, "invoices/settings.html", {"form": form, "profile": profile})
