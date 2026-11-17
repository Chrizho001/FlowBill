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


@pytest.mark.django_db
class TestRefreshTokenView:
    """Tests for POST /api/v1/auth/refresh/ (cookie-only rotation, H3)."""

    url = "/api/v1/auth/refresh/"

    def test_refresh_with_cookie_only_rotates_token(self, api_client, verified_user):
        login_res = api_client.post("/api/v1/auth/login/", {
            "email": verified_user.email,
            "password": "SecurePass123!",
        }, format="json")
        assert login_res.status_code == 200
        old_refresh_cookie = login_res.cookies["flowbill-refresh-token"].value

        # Ensure no Authorization header is sent (simulating expired access token)
        api_client.credentials()
        refresh_res = api_client.post(self.url)

        assert refresh_res.status_code == 200
        assert "access" in refresh_res.json()["data"]
        new_refresh_cookie = refresh_res.cookies["flowbill-refresh-token"].value
        assert new_refresh_cookie != old_refresh_cookie

        # Old refresh token is now blacklisted and cannot be reused
        api_client.cookies["flowbill-refresh-token"] = old_refresh_cookie
        reuse_res = api_client.post(self.url)
        assert reuse_res.status_code == 401

    def test_refresh_without_cookie_returns_401(self, api_client):
        response = api_client.post(self.url)
        assert response.status_code == 401
        assert response.json()["code"] == "REFRESH_TOKEN_MISSING"

    def test_refresh_succeeds_when_an_expired_access_token_is_sent(self, api_client, verified_user):
        """Clients refresh precisely when their access token has expired; a stale
        Authorization header must not cause JWT authentication to reject the call."""
        from datetime import timedelta
        from rest_framework_simplejwt.tokens import AccessToken

        login_res = api_client.post("/api/v1/auth/login/", {
            "email": verified_user.email,
            "password": "SecurePass123!",
        }, format="json")
        assert login_res.status_code == 200

        expired = AccessToken.for_user(verified_user)
        expired.set_exp(lifetime=-timedelta(minutes=1))
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {expired}")

        refresh_res = api_client.post(self.url)

        assert refresh_res.status_code == 200
        assert "access" in refresh_res.json()["data"]

    def test_refresh_issues_tokens_for_the_refresh_cookie_user_not_the_header_user(
        self, api_client, verified_user
    ):
        """Identity comes only from the refresh token. A valid access token for a
        different user in the Authorization header must not change who is refreshed."""
        from rest_framework_simplejwt.settings import api_settings
        from rest_framework_simplejwt.tokens import AccessToken

        other_user = User.objects.create_user(
            email="other@example.com",
            password="SecurePass123!",
            full_name="Other User",
        )
        other_user.is_verified = True
        other_user.save()

        login_res = api_client.post("/api/v1/auth/login/", {
            "email": verified_user.email,
            "password": "SecurePass123!",
        }, format="json")
        assert login_res.status_code == 200

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(other_user)}")
        refresh_res = api_client.post(self.url)

        assert refresh_res.status_code == 200
        new_access = AccessToken(refresh_res.json()["data"]["access"])
        assert str(new_access[api_settings.USER_ID_CLAIM]) == str(verified_user.id)


@pytest.mark.django_db
class TestSecurityHardeningAuth:
    """Tests for M2, M3, M5, L1, L6 security findings."""

    def test_password_reset_blacklists_outstanding_refresh_tokens(self, api_client, verified_user):
        cache.clear()
        login_res = api_client.post("/api/v1/auth/login/", {
            "email": verified_user.email,
            "password": "SecurePass123!",
        }, format="json")
        assert login_res.status_code == 200

        # Request & confirm password reset
        api_client.post("/api/v1/auth/password-reset/", {"email": verified_user.email}, format="json")
        record = cache.get(f"{PASSWORD_RESET_CACHE_PREFIX}{verified_user.email.lower()}")
        otp = record["otp"]

        confirm_res = api_client.post("/api/v1/auth/password-reset/confirm/", {
            "email": verified_user.email,
            "otp": otp,
            "password": "BrandNewPassword123!",
            "confirm_password": "BrandNewPassword123!",
        }, format="json")
        assert confirm_res.status_code == 200

        # Pre-reset refresh cookie should now be rejected (blacklisted)
        refresh_res = api_client.post("/api/v1/auth/refresh/")
        assert refresh_res.status_code == 401

    def test_resend_verification_unknown_email_returns_200_anti_enumeration(self, api_client):
        cache.clear()
        res = api_client.post(
            "/api/v1/auth/resend-verification/",
            {"email": "nonexistent@example.com"},
            format="json",
        )
        assert res.status_code == 200

    def test_common_password_rejected_by_django_validators(self, api_client):
        res = api_client.post("/api/v1/auth/register/", {
            "email": "brandnew@example.com",
            "full_name": "Brand New",
            "password": "Password1!",
            "confirm_password": "Password1!",
        }, format="json")
        assert res.status_code == 400
        assert "password" in res.json()["fields"]

    def test_schema_and_docs_blocked_when_debug_false(self, api_client):
        from django.test import override_settings

        with override_settings(DEBUG=False, EXPOSE_API_DOCS=False):
            schema_res = api_client.get("/api/schema/")
            docs_res = api_client.get("/api/docs/")
            assert schema_res.status_code == 401
            assert docs_res.status_code == 401

    def test_unhandled_exception_returns_standardized_500_envelope(self):
        from core.exceptions import flowbill_exception_handler

        response = flowbill_exception_handler(RuntimeError("unexpected crash"), {})
        assert response is not None
        assert response.status_code == 500
        assert response.data == {
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
            "fields": {},
        }