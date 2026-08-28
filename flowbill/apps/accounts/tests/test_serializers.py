import pytest
from django.contrib.auth import get_user_model
from apps.accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    VerifyEmailSerializer,
    ResendVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    BusinessProfileSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestRegisterSerializer:
    """Tests for the RegisterSerializer."""

    def get_valid_data(self):
        return {
            "email": "chris@example.com",
            "full_name": "Chris Friday",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
        }

    def test_valid_registration_data_passes(self):
        serializer = RegisterSerializer(data=self.get_valid_data())
        assert serializer.is_valid(), serializer.errors

    def test_mismatched_passwords_fail(self):
        data = self.get_valid_data()
        data["confirm_password"] = "WrongPassword123!"
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "confirm_password" in serializer.errors

    def test_invalid_email_fails(self):
        data = self.get_valid_data()
        data["email"] = "not-an-email"
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_weak_password_fails(self):
        data = self.get_valid_data()
        data["password"] = "123"
        data["confirm_password"] = "123"
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_duplicate_email_fails(self):
        User.objects.create_user(
            email="chris@example.com",
            password="SecurePass123!",
            full_name="Chris Friday",
        )
        serializer = RegisterSerializer(data=self.get_valid_data())
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_missing_full_name_fails(self):
        data = self.get_valid_data()
        del data["full_name"]
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "full_name" in serializer.errors

    def test_full_name_too_short_fails(self):
        data = self.get_valid_data()
        data["full_name"] = "A"
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "full_name" in serializer.errors

    def test_password_without_number_fails(self):
        data = self.get_valid_data()
        data["password"] = "NoNumbersHere!"
        data["confirm_password"] = "NoNumbersHere!"
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_password_without_special_char_fails(self):
        data = self.get_valid_data()
        data["password"] = "NoSpecialChar1"
        data["confirm_password"] = "NoSpecialChar1"
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors


@pytest.mark.django_db
class TestLoginSerializer:
    """Tests for the LoginSerializer."""

    def setup_method(self):
        self.user = User.objects.create_user(
            email="chris@example.com",
            password="SecurePass123!",
            full_name="Chris Friday",
        )

    def test_valid_credentials_pass(self):
        self.user.is_verified = True
        self.user.save()
        serializer = LoginSerializer(data={
            "email": "chris@example.com",
            "password": "SecurePass123!",
        })
        assert serializer.is_valid(), serializer.errors

    def test_wrong_password_fails(self):
        serializer = LoginSerializer(data={
            "email": "chris@example.com",
            "password": "WrongPassword!",
        })
        assert not serializer.is_valid()

    def test_unverified_user_cannot_login(self):
        serializer = LoginSerializer(data={
            "email": "chris@example.com",
            "password": "SecurePass123!",
        })
        assert not serializer.is_valid()
        assert "email" in serializer.errors or "non_field_errors" in serializer.errors

    def test_nonexistent_email_fails(self):
        serializer = LoginSerializer(data={
            "email": "nobody@example.com",
            "password": "SecurePass123!",
        })
        assert not serializer.is_valid()

    def test_missing_email_fails(self):
        serializer = LoginSerializer(data={"password": "SecurePass123!"})
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_missing_password_fails(self):
        serializer = LoginSerializer(data={"email": "chris@example.com"})
        assert not serializer.is_valid()
        assert "password" in serializer.errors


class TestVerifyEmailSerializer:
    """Tests for the VerifyEmailSerializer."""

    def test_valid_otp_passes(self):
        serializer = VerifyEmailSerializer(data={
            "email": "user@example.com",
            "otp": "123456",
        })
        assert serializer.is_valid(), serializer.errors

    def test_non_digit_otp_fails(self):
        serializer = VerifyEmailSerializer(data={
            "email": "user@example.com",
            "otp": "abcdef",
        })
        assert not serializer.is_valid()
        assert "otp" in serializer.errors

    def test_short_otp_fails(self):
        serializer = VerifyEmailSerializer(data={
            "email": "user@example.com",
            "otp": "12345",
        })
        assert not serializer.is_valid()
        assert "otp" in serializer.errors


class TestPasswordResetSerializers:
    """Tests for PasswordResetRequestSerializer and PasswordResetConfirmSerializer."""

    def test_reset_request_valid_email(self):
        serializer = PasswordResetRequestSerializer(data={"email": "user@example.com"})
        assert serializer.is_valid(), serializer.errors

    def test_reset_confirm_valid_data(self):
        serializer = PasswordResetConfirmSerializer(data={
            "email": "user@example.com",
            "otp": "654321",
            "password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!",
        })
        assert serializer.is_valid(), serializer.errors

    def test_reset_confirm_mismatched_password_fails(self):
        serializer = PasswordResetConfirmSerializer(data={
            "email": "user@example.com",
            "otp": "654321",
            "password": "NewSecurePass123!",
            "confirm_password": "DifferentPassword123!",
        })
        assert not serializer.is_valid()


class TestBusinessProfileSerializer:
    """Tests for BusinessProfileSerializer."""

    def test_valid_profile_data_passes(self):
        serializer = BusinessProfileSerializer(data={
            "business_name": "Apex Digital",
            "phone": "+1234567890",
            "country": "us",
            "default_currency": "USD",
            "default_payment_terms": "net_15",
            "bank_name": "Silicon Valley Bank",
        })
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["country"] == "US"

    def test_invalid_country_code_fails(self):
        serializer = BusinessProfileSerializer(data={
            "country": "USA",
        })
        assert not serializer.is_valid()
        assert "country" in serializer.errors