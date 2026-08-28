import pytest
from django.contrib.auth import get_user_model
from apps.accounts.models import BusinessProfile

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests for the custom User model."""

    def test_create_user_with_email_and_password(self):
        user = User.objects.create_user(
            email="chris@example.com",
            password="SecurePass123!",
            full_name="Chris Friday",
        )
        assert user.email == "chris@example.com"
        assert user.full_name == "Chris Friday"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_user_password_is_hashed(self):
        user = User.objects.create_user(
            email="chris@example.com",
            password="SecurePass123!",
            full_name="Chris Friday",
        )
        assert user.password != "SecurePass123!"
        assert user.check_password("SecurePass123!") is True

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(
            email="Chris@EXAMPLE.COM",
            password="SecurePass123!",
            full_name="Chris Friday",
        )
        assert user.email == "Chris@example.com"

    def test_create_user_without_email_raises_error(self):
        with pytest.raises(ValueError, match="Email address is required"):
            User.objects.create_user(email="", password="SecurePass123!", full_name="Chris Friday")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="admin@flowbill.com",
            password="AdminPass123!",
            full_name="Admin User",
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_verified is True

    def test_user_str_returns_email(self):
        user = User.objects.create_user(
            email="chris@example.com",
            password="SecurePass123!",
            full_name="Chris Friday",
        )
        assert str(user) == "chris@example.com"

    def test_user_first_name_property(self):
        user = User(full_name="Chris Friday")
        assert user.first_name == "Chris"

    def test_user_last_name_property(self):
        user = User(full_name="Chris Friday")
        assert user.last_name == "Friday"

    def test_user_last_name_property_with_multiple_names(self):
        user = User(full_name="Chris Friday Junior")
        assert user.last_name == "Friday Junior"

    def test_user_first_name_empty_full_name(self):
        user = User(full_name="")
        assert user.first_name == ""

    def test_user_id_is_uuid(self):
        user = User.objects.create_user(
            email="chris@example.com",
            password="SecurePass123!",
            full_name="Chris Friday",
        )
        import uuid
        assert isinstance(user.id, uuid.UUID)

    def test_two_users_cannot_share_email(self):
        from django.db import IntegrityError
        User.objects.create_user(
            email="chris@example.com",
            password="SecurePass123!",
            full_name="Chris Friday",
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email="chris@example.com",
                password="AnotherPass123!",
                full_name="Another Person",
            )


@pytest.mark.django_db
class TestBusinessProfileModel:
    """Tests for the BusinessProfile model."""

    def test_create_business_profile_linked_to_user(self):
        user = User.objects.create_user(
            email="developer@flowbill.com",
            password="SecurePass123!",
            full_name="Dev User",
        )
        profile = BusinessProfile.objects.create(
            user=user,
            business_name="Acme Consulting",
            phone="+1234567890",
            country="US",
            tax_id="TAX-123456",
            bank_name="Chase",
            bank_account_name="Acme Consulting LLC",
            bank_account_number="1234567890",
        )
        assert profile.user == user
        assert user.profile == profile
        assert profile.business_name == "Acme Consulting"
        assert profile.default_currency == "USD"
        assert profile.default_payment_terms == "net_30"

    def test_business_profile_str_returns_name(self):
        user = User.objects.create_user(
            email="developer@flowbill.com",
            password="SecurePass123!",
            full_name="Dev User",
        )
        profile = BusinessProfile.objects.create(
            user=user,
            business_name="Flow Studio",
        )
        assert str(profile) == "Flow Studio"

    def test_business_profile_cascade_deletion(self):
        user = User.objects.create_user(
            email="temp@flowbill.com",
            password="SecurePass123!",
            full_name="Temp User",
        )
        BusinessProfile.objects.create(user=user, business_name="Temp Biz")
        user_id = user.id
        user.delete()
        assert not BusinessProfile.objects.filter(user_id=user_id).exists()