from datetime import timedelta
from urllib.parse import quote

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, ProtectedError, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .emails import send_invoice_email
from .forms import BusinessProfileForm, ClientForm, InvoiceForm, ItemFormSet
from .models import BusinessProfile, Client, Invoice


def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    sent = Invoice.objects.filter(status=Invoice.SENT)
    paid = Invoice.objects.filter(status=Invoice.PAID)

    # One aggregate query per card instead of looping over every invoice.
    collected = paid.filter(paid_at__gte=month_start).aggregate(total=Sum("total"))["total"] or 0
    collected_before = paid.filter(
        paid_at__gte=last_month_start, paid_at__lt=month_start
    ).aggregate(total=Sum("total"))["total"] or 0

    outstanding = sent.aggregate(total=Sum("total"), count=Count("id"))
    overdue = sent.filter(due_date__lt=today).aggregate(total=Sum("total"), count=Count("id"))

    # Percentage change against last month, only when there's something to compare to.
    trend = None
    if collected_before:
        trend = round((collected - collected_before) / collected_before * 100)

    # Average days between issuing an invoice and getting paid.
    pay_days = []
    for issued, paid_on in paid.exclude(paid_at=None).values_list("issue_date", "paid_at")[:100]:
        pay_days.append((paid_on - issued).days)
    if pay_days:
        avg_days = round(sum(pay_days) / len(pay_days))
    else:
        avg_days = None

    # How much of what was billed this month has already come in.
    billed_this_month = Invoice.objects.exclude(status=Invoice.DRAFT).filter(issue_date__gte=month_start)
    billed = billed_this_month.aggregate(total=Sum("total"))["total"] or 0
    billed_paid = billed_this_month.filter(status=Invoice.PAID).aggregate(total=Sum("total"))["total"] or 0
    if billed:
        collection_rate = round(billed_paid / billed * 100)
    else:
        collection_rate = 0

    return render(request, "invoices/dashboard.html", {
        "greeting": _greeting(),
        "today": today,
        "has_invoices": Invoice.objects.exists(),
        "collected": collected,
        "trend": trend,
        "outstanding_total": outstanding["total"] or 0,
        "outstanding_count": outstanding["count"],
        "overdue_total": overdue["total"] or 0,
        "overdue_count": overdue["count"],
        "avg_days": avg_days,
        "billed": billed,
        "billed_paid": billed_paid,
        "collection_rate": collection_rate,
        "ring_dash": round(collection_rate * 2.136, 1),
        "monthly": _monthly_collected(month_start),
        "recent": Invoice.objects.select_related("client")[:6],
        "due_soon": _due_soon(today, BusinessProfile.load()),
    })


def _greeting():
    hour = timezone.localtime().hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    return "Good evening"


def _monthly_collected(month_start):
    """Money collected in each of the last six months, oldest first."""
    months = []
    start = month_start
    for i in range(6):
        months.insert(0, start)
        start = (start - timedelta(days=1)).replace(day=1)

    totals = (
        Invoice.objects.filter(status=Invoice.PAID, paid_at__gte=months[0])
        .annotate(month=TruncMonth("paid_at"))
        .values("month")
        .annotate(total=Sum("total"))
    )

    by_month = {}
    for row in totals:
        by_month[row["month"]] = float(row["total"])

    result = []
    for month in months:
        result.append({
            "label": month.strftime("%b"),
            "value": round(by_month.get(month, 0), 2),
        })
    return result


def _due_soon(today, business):
    upcoming = (
        Invoice.objects.select_related("client")
        .filter(status=Invoice.SENT, due_date__gte=today, due_date__lte=today + timedelta(days=7))
        .order_by("due_date")[:5]
    )
    rows = []
    for invoice in upcoming:
        rows.append({"invoice": invoice, "reminder": _reminder_link(invoice, business)})
    return rows


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

    # Once an invoice has gone to the client it shouldn't quietly change.
    if invoice.status != Invoice.DRAFT:
        messages.error(request, "Only drafts can be edited")
        return redirect("invoice_detail", pk=pk)

    return _invoice_form(request, invoice)


def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related("client"), pk=pk)

    return render(request, "invoices/invoice_detail.html", {
        "invoice": invoice,
        "items": invoice.items.all(),
        "reminder_link": _reminder_link(invoice, BusinessProfile.load()),
    })


@require_POST
def invoice_send(request, pk):
    """Email the invoice to the client. Drafts become 'sent' once it goes out."""
    invoice = get_object_or_404(Invoice.objects.select_related("client"), pk=pk)

    if invoice.status == Invoice.PAID:
        messages.error(request, "This invoice is already paid")
        return redirect("invoice_detail", pk=pk)

    try:
        send_invoice_email(invoice, BusinessProfile.load())
    except Exception as error:
        # Wrong password, no internet, blocked port... Keep the invoice as it
        # was and tell the user, instead of pretending it was sent.
        messages.error(request, f"Couldn't send the email ({error.__class__.__name__}). Check the email settings in .env")
        return redirect("invoice_detail", pk=pk)

    if invoice.status == Invoice.DRAFT:
        invoice.status = Invoice.SENT
        invoice.sent_at = timezone.localdate()
        invoice.save()
        messages.success(request, f"{invoice.number} emailed to {invoice.client.email}")
    else:
        messages.success(request, f"{invoice.number} sent again to {invoice.client.email}")

    return redirect("invoice_detail", pk=pk)


@require_POST
def invoice_status(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    action = request.POST.get("action")
    today = timezone.localdate()

    if action == "paid" and invoice.status == Invoice.SENT:
        invoice.status = Invoice.PAID
        invoice.paid_at = today
        messages.success(request, f"{invoice.number} marked as paid")
    elif action == "unpaid" and invoice.status == Invoice.PAID:
        # Handy when a payment bounces or was marked by mistake.
        invoice.status = Invoice.SENT
        invoice.paid_at = None
        messages.success(request, f"{invoice.number} moved back to awaiting payment")
    else:
        messages.error(request, "That change isn't allowed for this invoice")
        return redirect("invoice_detail", pk=pk)

    invoice.save()
    return redirect("invoice_detail", pk=pk)


@require_POST
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status != Invoice.DRAFT:
        messages.error(request, "Sent invoices are kept for your records and can't be deleted")
        return redirect("invoice_detail", pk=pk)

    number = invoice.number
    invoice.delete()
    messages.success(request, f"{number} deleted")
    return redirect("invoice_list")


def _reminder_link(invoice, business):
    """A mailto: link that opens the user's own email app with a polite reminder."""
    if invoice.status != Invoice.SENT:
        return ""

    client_name = invoice.client.name.split()[0]
    amount = f"${invoice.total:,.2f}"
    due = invoice.due_date.strftime("%B %d, %Y")

    if invoice.is_overdue:
        subject = f"Reminder: invoice {invoice.number} is overdue"
        opening = (
            f"This is a friendly reminder that invoice {invoice.number} for {amount} "
            f"was due on {due} and is now {invoice.days_overdue} days overdue."
        )
    else:
        subject = f"Invoice {invoice.number} due {due}"
        opening = f"Just a quick note that invoice {invoice.number} for {amount} is due on {due}."

    body = (
        f"Hi {client_name},\n\n"
        f"{opening}\n\n"
        "If you've already sent the payment, please ignore this message. "
        "Otherwise, let me know if you have any questions.\n\n"
        f"Thanks,\n{business.name}"
    )

    return f"mailto:{invoice.client.email}?subject={quote(subject)}&body={quote(body)}"


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
        return redirect("invoice_detail", pk=invoice.pk)

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
