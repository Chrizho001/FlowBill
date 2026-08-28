import structlog
from django.db import models
from django.conf import settings
from core.models import BaseModel

logger = structlog.get_logger(__name__)

CATEGORY_CHOICES = [
    ("software", "Software"),
    ("equipment", "Equipment"),
    ("marketing", "Marketing"),
    ("travel", "Travel"),
    ("education", "Education"),
    ("internet", "Internet"),
    ("other", "Other"),
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


class Expense(BaseModel):
    """
    Records a business expense for a freelancer.
    Flat model — no child records, no status workflow.
    Optionally linked to a client for project-based expense tracking.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expenses",
        db_index=True,
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="USD")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    description = models.CharField(max_length=500)
    date = models.DateField(db_index=True)
    receipt_url = models.URLField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "expenses"
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.description} — {self.currency} {self.amount}"