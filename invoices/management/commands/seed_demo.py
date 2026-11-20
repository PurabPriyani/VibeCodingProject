"""
Fills the app with believable sample data so the dashboard has something
to show during a demo.

    python manage.py seed_demo           # only runs on an empty database
    python manage.py seed_demo --reset   # wipes clients and invoices first
"""

import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from invoices.models import BusinessProfile, Client, Invoice, InvoiceItem

CLIENTS = [
    ("Sarah Chen", "Maple Bakery", "sarah@maplebakery.ca"),
    ("Daniel Okafor", "Northwind Studio", "daniel@northwind.studio"),
    ("Priya Nair", "Harbour Fitness", "priya@harbourfit.ca"),
    ("Tom Bergeron", "Lakeview Cafe", "tom@lakeviewcafe.ca"),
    ("Emma Walsh", "Pine and Co.", "emma@pineandco.ca"),
    ("Arjun Mehta", "Orbit Labs", "arjun@orbitlabs.io"),
    ("Chloe Martin", "Bloom Florals", "chloe@bloomflorals.ca"),
]

SERVICES = [
    ("Website design", Decimal("850.00")),
    ("Logo and brand kit", Decimal("420.00")),
    ("Social media graphics (set of 10)", Decimal("180.00")),
    ("Monthly site maintenance", Decimal("120.00")),
    ("Product photography (hour)", Decimal("65.00")),
    ("Menu redesign", Decimal("240.00")),
    ("Hosting setup", Decimal("75.00")),
    ("SEO audit", Decimal("300.00")),
]


class Command(BaseCommand):
    help = "Load sample clients and invoices for a demo."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing clients and invoices first.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Invoice.objects.all().delete()
            Client.objects.all().delete()
        elif Invoice.objects.exists():
            self.stdout.write(self.style.WARNING("There's already data here. Use --reset to start over."))
            return

        random.seed(7)  # same data every time, so screenshots are repeatable
        today = timezone.localdate()

        business = BusinessProfile.load()
        if business.name == "My Business":
            business.name = "Purab Studio"
            business.email = "hello@purabstudio.ca"
            business.phone = "705-555-0199"
            business.address = "45 Bayfield St\nBarrie, ON L4M 3A6"
            business.hst_number = "81234 5678 RT0001"
            business.save()

        clients = []
        for name, company, email in CLIENTS:
            clients.append(Client.objects.create(name=name, company=company, email=email, address="Barrie, ON"))

        # History: an invoice every few days for about six months, all paid.
        count = 0
        day = today - timedelta(days=170)
        while day < today - timedelta(days=30):
            terms = random.choice([7, 15, 15, 30])
            paid_on = day + timedelta(days=random.randint(3, terms + 6))
            self.make_invoice(business, random.choice(clients), day, terms, Invoice.PAID, paid_on)
            count += 1
            day += timedelta(days=random.randint(5, 9))

        # The last month is hand-picked so every part of the dashboard has
        # something in it: overdue, due this week, waiting, paid and a draft.
        recent = [
            (-28, 15, Invoice.SENT),   # overdue by about two weeks
            (-22, 15, Invoice.PAID),
            (-20, 15, Invoice.SENT),   # overdue by a few days
            (-16, 15, Invoice.PAID),
            (-12, 15, Invoice.SENT),   # due in a few days
            (-9, 15, Invoice.SENT),    # due later this week
            (-7, 30, Invoice.SENT),
            (-5, 7, Invoice.PAID),
            (-1, 15, Invoice.DRAFT),
        ]
        for offset, terms, status in recent:
            day = today + timedelta(days=offset)
            paid_on = None
            if status == Invoice.PAID:
                paid_on = min(day + timedelta(days=random.randint(2, 6)), today)
            self.make_invoice(business, random.choice(clients), day, terms, status, paid_on)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Added {len(clients)} clients and {count} invoices."))

    def make_invoice(self, business, client, day, terms, status, paid_on):
        invoice = Invoice.objects.create(client=client, issue_date=day, terms=terms)

        for service, price in random.sample(SERVICES, random.randint(1, 3)):
            InvoiceItem.objects.create(
                invoice=invoice,
                description=service,
                quantity=Decimal(random.choice([1, 1, 1, 2, 3])),
                unit_price=price,
            )
        invoice.recalculate(business)

        invoice.status = status
        if status != Invoice.DRAFT:
            invoice.sent_at = day
        invoice.paid_at = paid_on
        invoice.save()

        # created_at is filled in automatically with "now", which made the
        # activity timeline say an invoice was created after it was sent.
        created = timezone.make_aware(datetime.combine(day, time(9, 0)))
        Invoice.objects.filter(pk=invoice.pk).update(created_at=created)
