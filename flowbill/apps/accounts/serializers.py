import re
import structlog
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import BusinessProfile, CURRENCY_CHOICES, PAYMENT_TERMS_CHOICES

logger = structlog.get_logger(__name__)

User = get_user_model()


def validate_password_strength(value: str, user=None) -> str:
    """Reusable password strength validator combined with Django's AUTH_PASSWORD_VALIDATORS."""
    if len(value) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"\d", value):
        raise serializers.ValidationError("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise serializers.ValidationError("Password must contain at least one special character.")
    try:
        django_validate_password(value, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages))
    return value


class RegisterSerializer(serializers.Serializer):
    """Validates registration input."""

    email = serializers.EmailField()
    full_name = serializers.CharField(min_length=2, max_length=255)
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        normalized = value.lower().strip()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return normalized

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        candidate_user = User(
            email=attrs.get("email", ""),
            full_name=attrs.get("full_name", ""),
        )
        try:
            django_validate_password(attrs["password"], user=candidate_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs


class LoginSerializer(serializers.Serializer):
    """Validates login credentials and checks email verification status."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"].lower().strip()
        password = attrs["password"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": _("No account found with this email address.")}
            )

        if not user.check_password(password):
            logger.warning("auth.login_failed", email=email, reason="wrong_password")
            raise serializers.ValidationError(
                {"email": _("Invalid email or password.")}
            )

        if not user.is_verified:
            logger.warning("auth.login_blocked", email=email, reason="unverified")
            raise serializers.ValidationError(
                {"email": _("Please verify your email before logging in.")}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"email": _("This account has been deactivated.")}
            )

        attrs["user"] = user
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extends simplejwt's token serializer to embed user info."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        token["is_verified"] = user.is_verified
        return token


class UserDetailsSerializer(serializers.ModelSerializer):
    """Read-only user details returned on auth endpoints."""

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "is_verified", "created_at")
        read_only_fields = fields


class VerifyEmailSerializer(serializers.Serializer):
    """Validates 6-digit TOTP email verification."""

    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_email(self, value):
        return value.lower().strip()

    def validate_otp(self, value):
        if not re.match(r"^\d{6}$", value):
            raise serializers.ValidationError("Verification code must be a 6-digit number.")
        return value


class ResendVerificationSerializer(serializers.Serializer):
    """Validates email for resending verification OTP."""

    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Validates email for password reset request."""

    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validates OTP and new password for password reset."""

    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower().strip()

    def validate_otp(self, value):
        if not re.match(r"^\d{6}$", value):
            raise serializers.ValidationError("Reset code must be a 6-digit number.")
        return value

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        candidate_user = User(
            email=attrs.get("email", ""),
            full_name=attrs.get("full_name", ""),
        )
        try:
            django_validate_password(attrs["password"], user=candidate_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs


class BusinessProfileSerializer(serializers.ModelSerializer):
    """Serializer for BusinessProfile CRUD. The logo is read-only here (upload via /profile/logo/)."""

    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = BusinessProfile
        fields = (
            "id",
            "business_name",
            "logo_url",
            "phone",
            "website",
            "address",
            "city",
            "state",
            "country",
            "tax_id",
            "bank_name",
            "bank_account_name",
            "bank_account_number",
            "default_currency",
            "default_payment_terms",
            "payment_instructions",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "logo_url", "created_at", "updated_at")

    def get_logo_url(self, obj):
        if not obj.logo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url

    def validate_country(self, value):
        if value and len(value) != 2:
            raise serializers.ValidationError("Country must be a 2-letter ISO code.")
        return value.upper() if value else ""


class LogoUploadSerializer(serializers.Serializer):
    """
    Validates a business logo upload: size, real image content, allowed format and
    source dimensions, all checked before the image is decoded.
    """

    logo = serializers.FileField()

    def validate_logo(self, file):
        from django.conf import settings
        from PIL import Image, UnidentifiedImageError

        if file.size > settings.LOGO_MAX_UPLOAD_BYTES:
            raise serializers.ValidationError(
                f"Logo must be {settings.LOGO_MAX_UPLOAD_BYTES // 1024} KB or smaller."
            )

        allowed = ", ".join(f.replace("JPEG", "JPG") for f in settings.LOGO_ALLOWED_FORMATS)
        try:
            file.seek(0)
            image = Image.open(file)  # reads the header only
            fmt, (width, height) = image.format, image.size
        except (UnidentifiedImageError, OSError, ValueError):
            raise serializers.ValidationError(f"Upload a valid image file ({allowed}).")

        if fmt not in settings.LOGO_ALLOWED_FORMATS:
            raise serializers.ValidationError(f"Unsupported image type. Use {allowed}.")
        if width * height > settings.LOGO_MAX_SOURCE_PIXELS:
            raise serializers.ValidationError("Image dimensions are too large.")

        try:
            image.verify()  # integrity check; the image must be reopened afterwards
        except Exception:
            raise serializers.ValidationError(f"Upload a valid image file ({allowed}).")
        finally:
            file.seek(0)
        return file
