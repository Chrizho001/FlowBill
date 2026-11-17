import secrets
import structlog
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .models import BusinessProfile

logger = structlog.get_logger(__name__)

User = get_user_model()

# Expiration timeouts (in seconds)
OTP_EXPIRY = 60 * 15          # 15 minutes
COOLDOWN_EXPIRY = 60          # 60 seconds resend cooldown
PASSWORD_RESET_EXPIRY = 60 * 15
PASSWORD_RESET_COOLDOWN_EXPIRY = 60   # 60 seconds resend cooldown

OTP_CACHE_PREFIX = "email_verify_otp:"
COOLDOWN_CACHE_PREFIX = "email_verify_cooldown:"
PASSWORD_RESET_CACHE_PREFIX = "password_reset_otp:"
PASSWORD_RESET_COOLDOWN_PREFIX = "password_reset_cooldown:"


class AccountsService:
    """
    Handles all business logic for user authentication,
    verification OTPs, password resets, and business profiles.
    """

    @staticmethod
    def register_user(validated_data: dict) -> User:
        """
        Creates a new unverified user, creates a default business profile,
        generates a 6-digit TOTP, and sends a verification email.
        """
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
        )

        # Create initial business profile linked to user
        BusinessProfile.objects.create(
            user=user,
            business_name=user.full_name,
        )

        # Generate and dispatch 6-digit verification code
        otp = AccountsService._generate_verification_otp(user)
        AccountsService._send_verification_email(user, otp)

        logger.info(
            "accounts.user_registered",
            user_id=str(user.id),
            email=user.email,
        )

        return user

    @staticmethod
    def verify_email(email: str, otp: str) -> User:
        """
        Verifies a user's email using the 6-digit OTP code.
        Enforces 5 max attempts to prevent brute-forcing.
        """
        normalized_email = email.lower().strip()
        cache_key = f"{OTP_CACHE_PREFIX}{normalized_email}"
        record = cache.get(cache_key)

        if not record:
            logger.warning("accounts.verify_email_failed", email=normalized_email, reason="invalid_or_expired_otp")
            raise ValueError("This verification code is invalid or has expired.")

        attempts = record.get("attempts", 0)
        if attempts >= 5:
            cache.delete(cache_key)
            logger.warning("accounts.verify_email_locked", email=normalized_email, reason="max_attempts_exceeded")
            raise ValueError("Too many failed attempts. Please request a new verification code.")

        if not secrets.compare_digest(str(record.get("otp", "")), str(otp)):
            record["attempts"] = attempts + 1
            cache.set(cache_key, record, timeout=OTP_EXPIRY)
            logger.warning("accounts.verify_email_wrong_code", email=normalized_email, attempts=record["attempts"])
            raise ValueError("Invalid verification code.")

        try:
            user = User.objects.get(id=record["user_id"])
        except User.DoesNotExist:
            logger.error("accounts.verify_email.user_not_found", email=normalized_email, user_id=record["user_id"])
            raise ValueError("User not found.")

        if user.is_verified:
            logger.info("accounts.verify_email.already_verified", email=normalized_email, user_id=str(user.id))
            raise ValueError("This email has already been verified.")

        user.is_verified = True
        user.save(update_fields=["is_verified", "updated_at"])

        # Invalidate code immediately after successful verification
        cache.delete(cache_key)

        logger.info(
            "accounts.email_verified",
            user_id=str(user.id),
            email=user.email,
        )

        return user

    @staticmethod
    def resend_verification_otp(email: str) -> bool:
        """
        Resends a 6-digit verification code to an unverified user.
        Enforces a 60-second cooldown period between requests.
        Responds silently for unknown or already-verified emails to prevent
        account enumeration.
        """
        normalized_email = email.lower().strip()

        cooldown_key = f"{COOLDOWN_CACHE_PREFIX}{normalized_email}"
        if cache.get(cooldown_key):
            logger.warning("accounts.resend_verification.cooldown_active", email=normalized_email)
            raise ValueError("Please wait 60 seconds before requesting another code.")

        try:
            user = User.objects.get(email__iexact=normalized_email, is_active=True)
        except User.DoesNotExist:
            cache.set(cooldown_key, True, timeout=COOLDOWN_EXPIRY)
            logger.info("accounts.resend_verification.user_not_found", email=normalized_email)
            return True

        if user.is_verified:
            cache.set(cooldown_key, True, timeout=COOLDOWN_EXPIRY)
            logger.info("accounts.resend_verification.already_verified", email=normalized_email, user_id=str(user.id))
            return True

        otp = AccountsService._generate_verification_otp(user)
        AccountsService._send_verification_email(user, otp)

        logger.info("accounts.verification_code_resent", user_id=str(user.id), email=user.email)
        return True

    @staticmethod
    def request_password_reset(email: str) -> bool:
        """
        Initiates password reset by generating a 6-digit reset OTP and emailing it.
        Enforces a 60-second cooldown between sends, but fails silently (returns
        True) if the user does not exist or the cooldown is active, to avoid
        user enumeration.
        """
        normalized_email = email.lower().strip()

        try:
            user = User.objects.get(email__iexact=normalized_email, is_active=True)
        except User.DoesNotExist:
            # Silent return for security
            logger.info("accounts.password_reset_unknown_email", email=normalized_email)
            return True

        cooldown_key = f"{PASSWORD_RESET_COOLDOWN_PREFIX}{normalized_email}"
        if cache.get(cooldown_key):
            # Silent return — the endpoint must respond identically whether or
            # not an email is actually dispatched (anti-enumeration).
            logger.warning(
                "accounts.password_reset_cooldown_active",
                email=normalized_email,
                user_id=str(user.id),
            )
            return True

        otp = f"{secrets.randbelow(1000000):06d}"
        cache_key = f"{PASSWORD_RESET_CACHE_PREFIX}{normalized_email}"
        cache.set(
            cache_key,
            {"user_id": str(user.id), "otp": otp, "attempts": 0},
            timeout=PASSWORD_RESET_EXPIRY,
        )

        try:
            from apps.notifications.tasks import send_password_reset_email_task
            send_password_reset_email_task.delay(
                user_id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                otp=otp,
            )
        except Exception as e:
            logger.error("accounts.password_reset_email_failed", user_id=str(user.id), error=str(e))

        # Set resend cooldown only after a real dispatch attempt
        cache.set(cooldown_key, True, timeout=PASSWORD_RESET_COOLDOWN_EXPIRY)

        logger.info("accounts.password_reset_requested", user_id=str(user.id), email=user.email)
        return True

    @staticmethod
    def confirm_password_reset(email: str, otp: str, new_password: str) -> User:
        """
        Validates the password reset OTP and updates the user's password.
        """
        normalized_email = email.lower().strip()
        cache_key = f"{PASSWORD_RESET_CACHE_PREFIX}{normalized_email}"
        record = cache.get(cache_key)

        if not record:
            logger.warning("accounts.password_reset_confirm.invalid_or_expired", email=normalized_email)
            raise ValueError("This password reset code is invalid or has expired.")

        attempts = record.get("attempts", 0)
        if attempts >= 5:
            cache.delete(cache_key)
            logger.warning("accounts.password_reset_confirm.locked_out", email=normalized_email, attempts=attempts)
            raise ValueError("Too many failed attempts. Please request a new password reset code.")

        if not secrets.compare_digest(str(record.get("otp", "")), str(otp)):
            record["attempts"] = attempts + 1
            cache.set(cache_key, record, timeout=PASSWORD_RESET_EXPIRY)
            logger.warning("accounts.password_reset_confirm.wrong_code", email=normalized_email, attempts=record["attempts"])
            raise ValueError("Invalid reset code.")

        try:
            user = User.objects.get(id=record["user_id"])
        except User.DoesNotExist:
            logger.error("accounts.password_reset_confirm.user_not_found", email=normalized_email, user_id=record["user_id"])
            raise ValueError("User not found.")

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])

        # Invalidate all outstanding JWT refresh tokens for this user
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        for outstanding in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=outstanding)

        # Invalidate reset code
        cache.delete(cache_key)

        logger.info("accounts.password_reset_success", user_id=str(user.id), email=user.email)
        return user

    @staticmethod
    def get_or_create_profile(user: User) -> BusinessProfile:
        """Retrieves or provisions the 1:1 BusinessProfile for a user."""
        profile, created = BusinessProfile.objects.get_or_create(user=user)
        if created:
            logger.info("accounts.profile.auto_created", user_id=str(user.id), profile_id=str(profile.id))
        return profile

    @staticmethod
    def update_profile(user: User, validated_data: dict) -> BusinessProfile:
        """Updates the BusinessProfile fields for a user."""
        profile = AccountsService.get_or_create_profile(user)
        for field, value in validated_data.items():
            setattr(profile, field, value)
        profile.save()
        logger.info("accounts.profile_updated", user_id=str(user.id), profile_id=str(profile.id))
        return profile

    @staticmethod
    def set_logo(user: User, uploaded_file) -> BusinessProfile:
        """
        Re-encodes a validated logo upload to PNG and stores it on the profile.

        Re-encoding strips all metadata (EXIF, GPS, comments) and any payload
        hidden after the image data; the logo is shrunk to LOGO_MAX_DIMENSION.
        Validation (size, format, dimensions) happens in LogoUploadSerializer.
        """
        import io

        from django.conf import settings
        from django.core.files.base import ContentFile
        from PIL import Image, ImageOps

        uploaded_file.seek(0)
        with Image.open(uploaded_file) as source:
            image = ImageOps.exif_transpose(source)  # honour camera orientation, then drop EXIF
            has_alpha = image.mode in ("RGBA", "LA", "PA") or (
                image.mode == "P" and "transparency" in image.info
            )
            image = image.convert("RGBA" if has_alpha else "RGB")
            image.thumbnail((settings.LOGO_MAX_DIMENSION, settings.LOGO_MAX_DIMENSION))
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", optimize=True)

        profile = AccountsService.get_or_create_profile(user)
        old_name = profile.logo.name if profile.logo else None
        profile.logo.save("logo.png", ContentFile(buffer.getvalue()), save=False)
        profile.save(update_fields=["logo", "updated_at"])
        if old_name and old_name != profile.logo.name:
            profile.logo.storage.delete(old_name)

        logger.info(
            "accounts.logo_updated",
            user_id=str(user.id),
            profile_id=str(profile.id),
            size_bytes=len(buffer.getvalue()),
            dimensions=f"{image.width}x{image.height}",
        )
        return profile

    @staticmethod
    def remove_logo(user: User) -> BusinessProfile:
        """Deletes the profile's logo file and clears the field."""
        profile = AccountsService.get_or_create_profile(user)
        if profile.logo:
            name = profile.logo.name
            profile.logo.storage.delete(name)
            profile.logo = ""
            profile.save(update_fields=["logo", "updated_at"])
            logger.info("accounts.logo_removed", user_id=str(user.id), profile_id=str(profile.id))
        return profile

    @staticmethod
    def _generate_verification_otp(user: User) -> str:
        """Generates a cryptographically random 6-digit numeric OTP."""
        otp = f"{secrets.randbelow(1000000):06d}"
        normalized_email = user.email.lower().strip()

        # Cache verification record
        cache_key = f"{OTP_CACHE_PREFIX}{normalized_email}"
        cache.set(
            cache_key,
            {"user_id": str(user.id), "otp": otp, "attempts": 0},
            timeout=OTP_EXPIRY,
        )

        # Set resend cooldown
        cooldown_key = f"{COOLDOWN_CACHE_PREFIX}{normalized_email}"
        cache.set(cooldown_key, True, timeout=COOLDOWN_EXPIRY)

        return otp

    @staticmethod
    def _send_verification_email(user: User, otp: str) -> None:
        """Dispatches verification email via Celery async task."""
        try:
            from apps.notifications.tasks import send_verification_email_task
            send_verification_email_task.delay(
                user_id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                otp=otp,
            )
        except Exception as e:
            logger.error(
                "accounts.verification_email_failed",
                user_id=str(user.id),
                error=str(e),
            )