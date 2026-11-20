"""
Automated tests for Ledgerly, run by Django's test runner.

They cover the money maths, invoice numbering and statuses, the emails and
their PDF attachments, pagination, and that every page loads.
"""

from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .calculations import invoice_totals, money
from .models import BusinessProfile, Client, Invoice, InvoiceItem
from .templatetags.money import cad


class CalculationTests(TestCase):
    def test_rounds_half_cents_up(self):
        self.assertEqual(money(Decimal("2.345")), Decimal("2.35"))
        self.assertEqual(money(Decimal("0.5") * Decimal("2.01")), Decimal("1.01"))

    def test_tax_is_worked_out_on_the_subtotal(self):
        # 3 x 19.99 + 250 = 309.97, and 13% of that is 40.2961 -> 40.30
        subtotal, tax, total = invoice_totals([(3, "19.99"), (1, "250")], Decimal("13"))
        self.assertEqual(subtotal, Decimal("309.97"))
        self.assertEqual(tax, Decimal("40.30"))
        self.assertEqual(total, Decimal("350.27"))

    def test_no_tax(self):
        subtotal, tax, total = invoice_totals([(2, "50")], Decimal("0"))
        self.assertEqual(tax, Decimal("0.00"))
        self.assertEqual(total, Decimal("100.00"))

    def test_money_filter_always_uses_commas(self):
        self.assertEqual(cad(Decimal("5769.4")), "$5,769.40")
        self.assertEqual(cad(Decimal("5769.4"), 0), "$5,769")
        self.assertEqual(cad(None), "$0.00")


class InvoiceModelTests(TestCase):
    def setUp(self):
        self.client_record = Client.objects.create(name="Sarah Chen", company="Maple Bakery", email="s@maple.ca")

    def make_invoice(self, **extra):
        return Invoice.objects.create(client=self.client_record, **extra)

    def test_numbers_count_up_and_never_repeat(self):
        first = self.make_invoice()
        second = self.make_invoice()
        year = timezone.localdate().year
        self.assertEqual(first.number, f"INV-{year}-001")
        self.assertEqual(second.number, f"INV-{year}-002")

    def test_due_date_follows_terms(self):
        invoice = self.make_invoice(issue_date=timezone.localdate(), terms=30)
        self.assertEqual(invoice.due_date, invoice.issue_date + timedelta(days=30))

    def test_overdue_is_worked_out_from_the_due_date(self):
        old = timezone.localdate() - timedelta(days=40)
        invoice = self.make_invoice(issue_date=old, terms=15, status=Invoice.SENT)
        self.assertTrue(invoice.is_overdue)
        self.assertEqual(invoice.display_status, "overdue")

        invoice.status = Invoice.PAID
        self.assertFalse(invoice.is_overdue)

    def test_recalculate_respects_the_hst_switch(self):
        business = BusinessProfile.load()
        invoice = self.make_invoice()
        InvoiceItem.objects.create(invoice=invoice, description="Logo", quantity=1, unit_price=Decimal("100"))

        invoice.recalculate(business)
        self.assertEqual(invoice.total, Decimal("113.00"))

        business.charge_tax = False
        invoice.recalculate(business)
        self.assertEqual(invoice.total, Decimal("100.00"))


class InvoiceViewTests(TestCase):
    def setUp(self):
        self.client_record = Client.objects.create(name="Sarah Chen", email="s@maple.ca")

    def form_data(self, **items):
        data = {
            "client": self.client_record.pk,
            "issue_date": timezone.localdate().isoformat(),
            "terms": "15",
            "notes": "",
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "1",
            "items-MAX_NUM_FORMS": "1000",
        }
        data.update(items)
        return data

    def test_create_invoice_saves_totals(self):
        data = self.form_data(**{
            "items-0-description": "Website design",
            "items-0-quantity": "1",
            "items-0-unit_price": "800",
        })
        response = self.client.post(reverse("invoice_create"), data)
        invoice = Invoice.objects.get()
        self.assertRedirects(response, reverse("invoice_detail", args=[invoice.pk]))
        self.assertEqual(invoice.total, Decimal("904.00"))

    def test_invoice_needs_at_least_one_item(self):
        data = self.form_data(**{"items-0-description": "", "items-0-unit_price": ""})
        self.client.post(reverse("invoice_create"), data)
        self.assertFalse(Invoice.objects.exists())

    def test_negative_quantity_is_rejected(self):
        data = self.form_data(**{
            "items-0-description": "Logo",
            "items-0-quantity": "-2",
            "items-0-unit_price": "50",
        })
        self.client.post(reverse("invoice_create"), data)
        self.assertFalse(Invoice.objects.exists())

    def test_status_flow(self):
        invoice = Invoice.objects.create(client=self.client_record)
        url = reverse("invoice_status", args=[invoice.pk])

        # Can't jump straight from draft to paid.
        self.client.post(url, {"action": "paid"})
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.DRAFT)

        self.client.post(reverse("invoice_send", args=[invoice.pk]))
        self.client.post(url, {"action": "paid"})
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.PAID)
        self.assertIsNotNone(invoice.paid_at)

    def test_send_emails_the_client_and_marks_it_sent(self):
        invoice = Invoice.objects.create(client=self.client_record)
        self.client.post(reverse("invoice_send", args=[invoice.pk]))

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["s@maple.ca"])
        self.assertIn(invoice.number, mail.outbox[0].subject)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_HOST="127.0.0.1",
        EMAIL_PORT=1,
        EMAIL_TIMEOUT=2,
    )
    def test_invoice_stays_a_draft_if_the_email_fails(self):
        # Nothing listens on port 1, so the connection is refused.
        invoice = Invoice.objects.create(client=self.client_record)
        self.client.post(reverse("invoice_send", args=[invoice.pk]))

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.DRAFT)

    def test_emails_have_the_invoice_attached_as_a_pdf(self):
        invoice = Invoice.objects.create(client=self.client_record)
        InvoiceItem.objects.create(invoice=invoice, description="Logo", quantity=1, unit_price=Decimal("100"))
        self.client.post(reverse("invoice_send", args=[invoice.pk]))

        filename, content, mimetype = mail.outbox[0].attachments[0]
        self.assertEqual(filename, f"{invoice.number}.pdf")
        self.assertEqual(mimetype, "application/pdf")
        self.assertTrue(content.startswith(b"%PDF"))

    def test_reminder_is_emailed_with_the_invoice(self):
        old = timezone.localdate() - timedelta(days=30)
        invoice = Invoice.objects.create(client=self.client_record, issue_date=old, terms=15, status=Invoice.SENT)
        self.client.post(reverse("invoice_remind", args=[invoice.pk]))

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("past due", mail.outbox[0].subject)
        self.assertIn("15 days past due", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].attachments[0][0], f"{invoice.number}.pdf")

    def test_drafts_cannot_get_reminders(self):
        invoice = Invoice.objects.create(client=self.client_record)
        self.client.post(reverse("invoice_remind", args=[invoice.pk]))
        self.assertEqual(len(mail.outbox), 0)

    def test_sent_invoices_cannot_be_edited_or_deleted(self):
        invoice = Invoice.objects.create(client=self.client_record, status=Invoice.SENT)

        response = self.client.get(reverse("invoice_edit", args=[invoice.pk]))
        self.assertRedirects(response, reverse("invoice_detail", args=[invoice.pk]))

        self.client.post(reverse("invoice_delete", args=[invoice.pk]))
        self.assertTrue(Invoice.objects.filter(pk=invoice.pk).exists())

    def test_client_with_invoices_is_not_deleted(self):
        Invoice.objects.create(client=self.client_record)
        self.client.post(reverse("client_delete", args=[self.client_record.pk]))
        self.assertTrue(Client.objects.filter(pk=self.client_record.pk).exists())

    def test_invoice_list_shows_ten_per_page(self):
        for i in range(12):
            Invoice.objects.create(client=self.client_record)

        first = self.client.get(reverse("invoice_list"))
        self.assertEqual(len(first.context["page"].object_list), 10)

        # The JavaScript asks for page 2 with this header and gets only the table back.
        second = self.client.get(reverse("invoice_list") + "?page=2", HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(len(second.context["page"].object_list), 2)
        self.assertNotContains(second, "<html")

    def test_invoice_search_looks_past_the_first_page(self):
        other = Client.objects.create(name="Arjun Mehta", company="Orbit Labs", email="a@orbit.io")
        for i in range(12):
            Invoice.objects.create(client=self.client_record)
        Invoice.objects.create(client=other)

        response = self.client.get(reverse("invoice_list") + "?q=orbit")
        self.assertEqual(response.context["page"].paginator.count, 1)

    def test_every_page_loads(self):
        Invoice.objects.create(client=self.client_record, status=Invoice.SENT)
        for name in ["dashboard", "invoice_list", "invoice_create", "client_list", "settings"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
