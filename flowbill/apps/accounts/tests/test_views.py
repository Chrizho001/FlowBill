import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from apps.accounts.models import BusinessProfile
from apps.accounts.services import AccountsService, OTP_CACHE_PREFIX, PASSWORD_RESET_CACHE_PREFIX, COOLDOWN_CACHE_PREFIX

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def verified_user(db):
    user = User.objects.create_user(
        email="chris@example.com",
        password="SecurePass123!",
        full_name="Chris Friday",
    )
    user.is_verified = True
    user.save()
    BusinessProfile.objects.get_or_create(user=user, business_name="Chris Friday Studio")
    return user


@pytest.fixture
def unverified_user(db):
    user = User.objects.create_user(
        email="unverified@example.com",
        password="SecurePass123!",
        full_name="Unverified User",
    )
    BusinessProfile.objects.get_or_create(user=user, business_name="Unverified Biz")
    return user


@pytest.mark.django_db
class TestRegisterView:
    """Tests for POST /api/v1/auth/register/"""

    url = "/api/v1/auth/register/"

    def get_valid_payload(self):
        return {
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
        }

    def test_successful_registration_returns_201(self, api_client):
        response = api_client.post(self.url, self.get_valid_payload(), format="json")
        assert response.status_code == 201
        assert User.objects.filter(email="newuser@example.com").exists()
        user = User.objects.get(email="newuser@example.com")
        assert user.is_verified is False
        assert BusinessProfile.objects.filter(user=user).exists()

    def test_duplicate_email_returns_400(self, api_client, verified_user):
        payload = self.get_valid_payload()
        payload["email"] = verified_user.email
        response = api_client.post(self.url, payload, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginView:
    """Tests for POST /api/v1/auth/login/"""

    url = "/api/v1/auth/login/"

    def test_verified_user_can_login(self, api_client, verified_user):
        response = api_client.post(self.url, {
            "email": verified_user.email,
            "password": "SecurePass123!",
        }, format="json")
        assert response.status_code == 200
        assert "access" in response.json()["data"]

    def test_unverified_user_cannot_login(self, api_client, unverified_user):
        response = api_client.post(self.url, {
            "email": unverified_user.email,
            "password": "SecurePass123!",
        }, format="json")
        assert response.status_code == 403


@pytest.mark.django_db
class TestLogoutView:
    """Tests for POST /api/v1/auth/logout/"""

    url = "/api/v1/auth/logout/"

    def test_logout_requires_authentication(self, api_client):
        response = api_client.post(self.url)
        assert response.status_code == 401

    def test_authenticated_user_can_logout(self, api_client, verified_user):
        login_response = api_client.post("/api/v1/auth/login/", {
            "email": verified_user.email,
            "password": "SecurePass123!",
        }, format="json")
        token = login_response.json()["data"]["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = api_client.post(self.url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestVerifyEmailView:
    """Tests for POST /api/v1/auth/verify-email/"""

    url = "/api/v1/auth/verify-email/"

    def test_successful_otp_verification(self, api_client, unverified_user):
        otp = AccountsService._generate_verification_otp(unverified_user)
        response = api_client.post(self.url, {
            "email": unverified_user.email,
            "otp": otp,
        }, format="json")

        assert response.status_code == 200
        unverified_user.refresh_from_db()
        assert unverified_user.is_verified is True

    def test_invalid_otp_returns_400(self, api_client, unverified_user):
        AccountsService._generate_verification_otp(unverified_user)
        response = api_client.post(self.url, {
            "email": unverified_user.email,
            "otp": "999999",
        }, format="json")

        assert response.status_code == 400
        assert response.json()["code"] == "VERIFICATION_FAILED"

    def test_expired_or_nonexistent_otp_returns_400(self, api_client):
        response = api_client.post(self.url, {
            "email": "nobody@example.com",
            "otp": "123456",
        }, format="json")

        assert response.status_code == 400

    def test_brute_force_lockout_after_five_attempts(self, api_client, unverified_user):
        AccountsService._generate_verification_otp(unverified_user)

        # 5 failed attempts
        for _ in range(5):
            api_client.post(self.url, {
                "email": unverified_user.email,
                "otp": "000000",
            }, format="json")

        # 6th attempt should return lockout
        response = api_client.post(self.url, {
            "email": unverified_user.email,
            "otp": "000000",
        }, format="json")

        assert response.status_code == 400
        assert "Too many failed attempts" in response.json()["message"]


@pytest.mark.django_db
class TestResendVerificationView:
    """Tests for POST /api/v1/auth/resend-verification/"""

    url = "/api/v1/auth/resend-verification/"

    def test_resend_verification_otp_success(self, api_client, unverified_user):
        # Clear any initial cooldown
        cache.delete(f"{COOLDOWN_CACHE_PREFIX}{unverified_user.email.lower()}")

        response = api_client.post(self.url, {"email": unverified_user.email}, format="json")
        assert response.status_code == 200

    def test_resend_cooldown_enforcement(self, api_client, unverified_user):
        # Trigger one generation (sets cooldown)
        AccountsService._generate_verification_otp(unverified_user)

        response = api_client.post(self.url, {"email": unverified_user.email}, format="json")
        assert response.status_code == 400
        assert "60 seconds" in response.json()["message"]


@pytest.mark.django_db
class TestPasswordResetViews:
    """Tests for Password Reset Request & Confirmation."""

    request_url = "/api/v1/auth/password-reset/"
    confirm_url = "/api/v1/auth/password-reset/confirm/"

    def test_password_reset_flow_success(self, api_client, verified_user):
        # 1. Request reset
        req_res = api_client.post(self.request_url, {"email": verified_user.email}, format="json")
        assert req_res.status_code == 200

        # Retrieve generated OTP from cache
        cache_key = f"{PASSWORD_RESET_CACHE_PREFIX}{verified_user.email.lower()}"
        record = cache.get(cache_key)
        assert record is not None
        otp = record["otp"]

        # 2. Confirm reset
        confirm_res = api_client.post(self.confirm_url, {
            "email": verified_user.email,
            "otp": otp,
            "password": "BrandNewPassword123!",
            "confirm_password": "BrandNewPassword123!",
        }, format="json")

        assert confirm_res.status_code == 200

        # 3. Login with new password
        login_res = api_client.post("/api/v1/auth/login/", {
            "email": verified_user.email,
            "password": "BrandNewPassword123!",
        }, format="json")
        assert login_res.status_code == 200


@pytest.mark.django_db
class TestBusinessProfileView:
    """Tests for GET / PUT / PATCH /api/v1/auth/profile/"""

    url = "/api/v1/auth/profile/"

    def test_unauthenticated_user_cannot_access_profile(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_authenticated_user_can_get_profile(self, api_client, verified_user):
        login_res = api_client.post("/api/v1/auth/login/", {
            "email": verified_user.email,
            "password": "SecurePass123!",
        }, format="json")
        token = login_res.json()["data"]["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(self.url)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["business_name"] == "Chris Friday Studio"

    def test_authenticated_user_can_update_profile(self, api_client, verified_user):
        login_res = api_client.post("/api/v1/auth/login/", {
            "email": verified_user.email,
            "password": "SecurePass123!",
        }, format="json")
        token = login_res.json()["data"]["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        update_payload = {
            "business_name": "Updated Agency Name",
            "phone": "+1987654321",
            "country": "US",
            "bank_name": "Chase Bank",
            "bank_account_name": "Updated Agency LLC",
            "bank_account_number": "9876543210",
            "default_currency": "EUR",
            "payment_instructions": "Wire transfer within 15 days.",
        }
        response = api_client.put(self.url, update_payload, format="json")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["business_name"] == "Updated Agency Name"
        assert data["default_currency"] == "EUR"
        assert data["payment_instructions"] == "Wire transfer within 15 days."