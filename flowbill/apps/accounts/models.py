import uuid6
import structlog
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
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

PAYMENT_TERMS_CHOICES = [
    ("due_on_receipt", "Due on Receipt"),
    ("net_15", "Net 15"),
    ("net_30", "Net 30"),
    ("net_60", "Net 60"),
]


class UserManager(BaseUserManager):
    """Custom manager — email is the unique identifier, not username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        logger.info("user.created", email=email, user_id=str(user.id))
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for FlowBill.
    Uses email as the primary identifier instead of username.
    Each user owns a BusinessProfile and tenant-scoped data.
    """

    id = models.UUIDField(primary_key=True, default=uuid6.uuid7, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def first_name(self):
        """allauth compatibility — returns first part of full_name."""
        return self.full_name.split()[0] if self.full_name else ""

    @property
    def last_name(self):
        """allauth compatibility — returns remainder of full_name."""
        parts = self.full_name.split()
        return " ".join(parts[1:]) if len(parts) > 1 else ""


class BusinessProfile(BaseModel):
    """
    1:1 Business profile holding branding, contact info, tax ID, and banking details.
    Rendered directly onto invoice PDFs and client portal views.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    business_name = models.CharField(max_length=255, blank=True, default="")
    logo_url = models.URLField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    website = models.URLField(blank=True, default="")
    address = models.CharField(max_length=500, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=2, blank=True, default="")
    tax_id = models.CharField(max_length=50, blank=True, default="")

    bank_name = models.CharField(max_length=100, blank=True, default="")
    bank_account_name = models.CharField(max_length=255, blank=True, default="")
    bank_account_number = models.CharField(max_length=50, blank=True, default="")

    default_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="USD",
    )
    default_payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS_CHOICES,
        default="net_30",
    )
    payment_instructions = models.TextField(blank=True, default="")

    class Meta:
        db_table = "business_profiles"
        verbose_name = "Business Profile"
        verbose_name_plural = "Business Profiles"

    def __str__(self):
        return self.business_name or f"{self.user.email}'s Profile"