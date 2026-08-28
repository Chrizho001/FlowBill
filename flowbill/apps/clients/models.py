import uuid6
import structlog
from django.db import models
from django.conf import settings
from core.models import BaseModel

logger = structlog.get_logger(__name__)

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

STATUS_CHOICES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
]


class Client(BaseModel):
    """
    Represents a client belonging to a FlowBill user (tenant).
    One user can have many clients.
    Email uniqueness is enforced per owner, not globally.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clients",
        db_index=True,
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20, blank=True, default="")
    company_name = models.CharField(max_length=255, blank=True, default="")
    website = models.URLField(blank=True, default="")
    address = models.CharField(max_length=500, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=2, blank=True, default="")
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="USD",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="active",
        db_index=True,
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "clients"
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "email"],
                condition=models.Q(is_deleted=False),
                name="unique_active_client_email_per_owner",
            )
        ]

    def __str__(self):
        if self.company_name:
            return f"{self.name} ({self.company_name})"
        return self.name

    @property
    def display_name(self):
        return self.company_name if self.company_name else self.name