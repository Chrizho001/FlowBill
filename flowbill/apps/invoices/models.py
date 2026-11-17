import re

import structlog
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import BaseModel

logger = structlog.get_logger(__name__)

INVOICE_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("pending", "Pending"),
    ("paid", "Paid"),
    ("overdue", "Overdue"),
    ("cancelled", "Cancelled"),
]

PAYMENT_TERMS_CHOICES = [
    ("due_on_receipt", "Due on Receipt"),
    ("net_15", "Net 15"),
    ("net_30", "Net 30"),
    ("net_60", "Net 60"),
]

CURRENCY_CHOICES = [
    ("USD", "US Dollar"),
    ("NGN", "Nigerian Naira"),
    ("GBP", "British Pound"),
    ("EUR", "Euro"),
    ("CAD", "Canadian Dollar"),
    ("AUD", "Australian Dollar"),
    ("GHS", "Ghanaian Cedi"),
    ("KES", "Kenyan Shilling"),
    ("ZAR", "South African Rand"),
]

EVENT_TYPE_CHOICES = [
    ("created", "Created"),
    ("sent", "Sent"),
    ("viewed", "Viewed"),
    ("paid", "Paid"),
    ("cancelled", "Cancelled"),
    ("overdue", "Marked Overdue"),
    ("duplicated", "Duplicated"),
]


INVOICE_NUMBER_RE = re.compile(r"^INV-(?P<year>\d{4})-(?P<seq>\d+)$")


def format_invoice_number(year: int, seq: int) -> str:
    """INV-YYYY-XXXX, zero-padded to 4 digits and growing past 9999."""
    return f"INV-{year}-{seq:04d}"


class InvoiceSequence(models.Model):
    """
    Per-year invoice number counter (INV-YYYY-XXXX is sequential per year, globally).

    One row per year is row-locked and incremented in the same transaction as the
    invoice insert, so allocation is O(1), concurrent creates queue on a single row
    instead of scanning/locking every invoice, and a rolled-back create releases its
    number (no gaps). Infrastructure table, not tenant data: it deliberately does not
    inherit BaseModel (no owner, soft delete or UUID key).
    """

    year = models.PositiveIntegerField(primary_key=True)
    last_value = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "invoice_sequences"

    def __str__(self):
        return f"{self.year}: {self.last_value}"

    @classmethod
    def _ensure_row(cls, year: int) -> None:
        # INSERT ... ON CONFLICT DO NOTHING: safe when two transactions start a new year at once.
        cls.objects.bulk_create([cls(year=year, last_value=0)], ignore_conflicts=True)

    @classmethod
    def next_value(cls, year: int) -> int:
        """Increment and return the year's counter. Must run inside a transaction."""
        cls._ensure_row(year)
        # UPDATE takes the row lock; concurrent callers wait here until we commit.
        cls.objects.filter(year=year).update(last_value=models.F("last_value") + 1)
        return cls.objects.values_list("last_value", flat=True).get(year=year)

    @classmethod
    def advance_to(cls, year: int, seq: int) -> None:
        """Make sure the counter is at least `seq` (for explicitly numbered invoices)."""
        cls._ensure_row(year)
        cls.objects.filter(year=year, last_value__lt=seq).update(last_value=seq)


class Invoice(BaseModel):
    """
    Core invoice model. Totals are always calculated server-side.
    Only draft invoices can be edited. Number is auto-generated and immutable.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoices",
        db_index=True,
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    number = models.CharField(max_length=20, unique=True, db_index=True)
    status = models.CharField(
        max_length=10,
        choices=INVOICE_STATUS_CHOICES,
        default="draft",
        db_index=True,
    )
    issue_date = models.DateField()
    due_date = models.DateField(db_index=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="USD")
    exchange_rate = models.DecimalField(
        max_digits=12, decimal_places=6, default=Decimal("1.000000")
    )

    # Totals — always calculated by InvoiceService, never set directly
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    tax_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    discount_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    notes = models.TextField(blank=True, default="")
    payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS_CHOICES,
        default="net_30",
    )

    class Meta:
        db_table = "invoices"
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number} — {self.client.name}"

    @property
    def is_overdue(self):
        from datetime import date

        if self.status in ("paid", "cancelled", "draft"):
            return False
        return self.due_date < date.today()

    def save(self, *args, **kwargs):
        from django.db import transaction

        if not self.number:
            # Allocate and insert in one transaction: the counter row stays locked
            # until commit, and a failed insert rolls the increment back (gapless).
            with transaction.atomic():
                year = timezone.now().year
                self.number = format_invoice_number(year, InvoiceSequence.next_value(year))
                return super().save(*args, **kwargs)

        if self._state.adding:
            # Explicit number on create (imports, fixtures): keep the counter ahead of it.
            match = INVOICE_NUMBER_RE.match(self.number)
            if match:
                with transaction.atomic():
                    InvoiceSequence.advance_to(int(match["year"]), int(match["seq"]))
                    return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)


class LineItem(models.Model):
    """
    A single line in an invoice.
    Total is always calculated as quantity × unit_price.
    Tax is per-line and stored as a percentage.
    """

    import uuid6 as _uuid6

    id = models.UUIDField(primary_key=True, default=_uuid6.uuid7, editable=False)

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoice_line_items"
        verbose_name = "Line Item"
        verbose_name_plural = "Line Items"

    def __str__(self):
        return f"{self.description} — {self.total}"

    def calculate_total(self):
        qty = Decimal(str(self.quantity)) if self.quantity is not None else Decimal("0.00")
        price = Decimal(str(self.unit_price)) if self.unit_price is not None else Decimal("0.00")
        return (qty * price).quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        self.total = self.calculate_total()
        super().save(*args, **kwargs)


class InvoiceEvent(models.Model):
    """
    Append-only audit log for invoice state changes.
    Never update or delete rows in this table.
    """

    import uuid6 as _uuid6

    id = models.UUIDField(primary_key=True, default=_uuid6.uuid7, editable=False)

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    description = models.CharField(max_length=500)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoice_events"
        verbose_name = "Invoice Event"
        verbose_name_plural = "Invoice Events"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.invoice.number} — {self.event_type}"
