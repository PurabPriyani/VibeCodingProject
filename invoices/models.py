from datetime import timedelta
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .calculations import money, invoice_totals


class BusinessProfile(models.Model):
    """The 'From' details printed on every invoice. There is only ever one row."""

    name = models.CharField(max_length=120, default="My Business")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    hst_number = models.CharField("HST number", max_length=30, blank=True)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("13.00"),
        validators=[MinValueValidator(0)],
    )
    charge_tax = models.BooleanField(
        default=True,
        help_text="Turn this off if you're a small supplier not registered for HST.",
    )

    def __str__(self):
        return self.name

    @property
    def initials(self):
        words = self.name.split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        return self.name[:2].upper()

    @classmethod
    def load(cls):
        # Always work with row 1 so the app never ends up with two profiles.
        profile, _ = cls.objects.get_or_create(pk=1)
        return profile


class Client(models.Model):
    name = models.CharField(max_length=120)
    company = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.company or self.name

    @property
    def initials(self):
        parts = str(self).split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return str(self)[:2].upper()


class Invoice(models.Model):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    STATUS_CHOICES = [(DRAFT, "Draft"), (SENT, "Sent"), (PAID, "Paid")]

    TERMS_CHOICES = [
        (0, "Due on receipt"),
        (7, "Net 7"),
        (15, "Net 15"),
        (30, "Net 30"),
    ]

    number = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="invoices")
    issue_date = models.DateField(default=timezone.localdate)
    terms = models.PositiveSmallIntegerField(choices=TERMS_CHOICES, default=15)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    notes = models.TextField(blank=True)

    # Totals are stored, not just calculated on the fly. That keeps the
    # dashboard fast (one SUM query) and an invoice never changes once sent,
    # even if the tax rate in settings changes later.
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

    sent_at = models.DateField(null=True, blank=True)
    paid_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issue_date", "-number"]

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = Invoice.next_number(self.issue_date.year)
        self.due_date = self.issue_date + timedelta(days=self.terms)
        super().save(*args, **kwargs)

    @staticmethod
    def next_number(year):
        """INV-2026-001, INV-2026-002 ... the counter starts again each year."""
        prefix = f"INV-{year}-"
        last = (
            Invoice.objects.filter(number__startswith=prefix)
            .order_by("-number")
            .values_list("number", flat=True)
            .first()
        )
        if last:
            count = int(last.split("-")[-1]) + 1
        else:
            count = 1
        return f"{prefix}{count:03d}"

    def recalculate(self, business):
        """Work out the totals from the saved line items and store them."""
        rows = []
        for item in self.items.all():
            rows.append((item.quantity, item.unit_price))

        if business.charge_tax:
            self.tax_rate = business.tax_rate
        else:
            self.tax_rate = Decimal("0")

        self.subtotal, self.tax_amount, self.total = invoice_totals(rows, self.tax_rate)
        self.save(update_fields=["tax_rate", "subtotal", "tax_amount", "total"])

    @property
    def is_overdue(self):
        return self.status == self.SENT and self.due_date < timezone.localdate()

    @property
    def display_status(self):
        # "Overdue" is never stored. It's worked out from the due date every
        # time, so it can't get out of sync.
        if self.is_overdue:
            return "overdue"
        return self.status

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (timezone.localdate() - self.due_date).days


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.description

    @property
    def line_total(self):
        return money(self.quantity * self.unit_price)
