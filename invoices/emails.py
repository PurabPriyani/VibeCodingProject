from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_invoice_email(invoice, business):
    """
    Email the invoice to the client.

    The message goes out with a plain-text version and an HTML version, so
    it reads fine in any email app. Replies go to the business email from
    Settings, not to whatever address the app sends from.
    """
    context = {
        "invoice": invoice,
        "items": invoice.items.all(),
        "business": business,
        "first_name": invoice.client.name.split()[0],
    }

    subject = f"Invoice {invoice.number} from {business.name}"
    text_body = render_to_string("emails/invoice.txt", context)
    html_body = render_to_string("emails/invoice.html", context)

    reply_to = []
    if business.email:
        reply_to.append(business.email)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invoice.client.email],
        reply_to=reply_to,
    )
    message.attach_alternative(html_body, "text/html")

    # fail_silently=False so the view knows when sending didn't work and
    # doesn't mark the invoice as sent by mistake.
    message.send(fail_silently=False)
