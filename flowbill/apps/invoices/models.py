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

    def generate_number(self):
        """
        Auto-generates invoice number in format INV-YYYY-XXXX.
        Sequential per year across all invoices — not per user.
        Uses integer sequence extraction rather than lexicographic string Max
        so sequences above 9999 sort accurately.
        """
        from django.db import connection

        year = timezone.now().year
        prefix = f"INV-{year}-"

        qs = Invoice.objects.filter(number__startswith=prefix)
        if connection.in_atomic_block:
            qs = qs.select_for_update()

        existing_numbers = qs.values_list("number", flat=True)
        max_seq = 0
        for num in existing_numbers:
            try:
                seq = int(num.rsplit("-", 1)[-1])
                if seq > max_seq:
                    max_seq = seq
            except (ValueError, IndexError):
                continue

        next_seq = max_seq + 1
        return f"{prefix}{next_seq:04d}"

    def save(self, *args, **kwargs):
        from django.db import IntegrityError, transaction

        if not self.number:
            for attempt in range(5):
                try:
                    with transaction.atomic():
                        self.number = self.generate_number()
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.number = ""
                    if attempt == 4:
                        raise
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
