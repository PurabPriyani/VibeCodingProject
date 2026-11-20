from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .pdf import build_invoice_pdf


def _send(invoice, business, subject, template, extra=None):
    """
    Shared by every email the app sends about an invoice.

    Each message has a plain-text version and an HTML version, so it reads
    fine in any email app, and the invoice itself is attached as a PDF.
    Replies go to the business email from Settings, not to whatever address
    the app sends from.
    """
    context = {
        "invoice": invoice,
        "items": invoice.items.all(),
        "business": business,
        "first_name": invoice.client.name.split()[0],
    }
    if extra:
        context.update(extra)

    reply_to = []
    if business.email:
        reply_to.append(business.email)

    message = EmailMultiAlternatives(
        subject=subject,
        body=render_to_string(f"emails/{template}.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invoice.client.email],
        reply_to=reply_to,
    )
    message.attach_alternative(render_to_string(f"emails/{template}.html", context), "text/html")
    message.attach(f"{invoice.number}.pdf", build_invoice_pdf(invoice, business), "application/pdf")

    # fail_silently=False so the view knows when sending didn't work and
    # doesn't tell the user it went out when it didn't.
    message.send(fail_silently=False)


def send_invoice_email(invoice, business):
    subject = f"Invoice {invoice.number} from {business.name}"
    _send(invoice, business, subject, "invoice")


def send_reminder_email(invoice, business):
    """A polite nudge. The wording changes depending on whether it's late yet."""
    due = invoice.due_date.strftime("%B %d, %Y").replace(" 0", " ")

    if invoice.is_overdue:
        subject = f"Friendly reminder: invoice {invoice.number} is past due"
    else:
        subject = f"Reminder: invoice {invoice.number} is due on {due}"

    _send(invoice, business, subject, "reminder", {"due": due})
