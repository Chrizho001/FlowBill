import pytest
from unittest import mock
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.models import BusinessProfile
from apps.accounts.services import (
    AccountsService,
    PASSWORD_RESET_CACHE_PREFIX,
    PASSWORD_RESET_COOLDOWN_PREFIX,
)

User = get_user_model()

# Tightened throttle rates used to exercise the throttling machinery quickly.
# Built on top of the live REST_FRAMEWORK dict so other DRF settings
# (exception handler, auth classes, pagination) are preserved.
_ALL_SCOPES = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]

_TIGHT_ALL = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {k: "2/min" for k in _ALL_SCOPES}}
_TIGHT_ANON = {
    **settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {**_ALL_SCOPES, "anon": "2/min", "user": "1000/sec"},
}
_TIGHT_USER = {
    **settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {**_ALL_SCOPES, "user": "2/min", "anon": "1000/sec"},
}


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


@pytest.fixture(autouse=True)
def clear_cache():
    """Throttle buckets and OTP records live in the cache — start each test clean."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestScopedAuthThrottling:
    """Each unauthenticated auth endpoint enforces its own scoped throttle."""

    @pytest.fixture(autouse=True)
    def tight_throttles(self):
        with override_settings(REST_FRAMEWORK=_TIGHT_ALL):
            yield

    CASES = [
        ("register", "/api/v1/auth/register/", {}),
        ("auth_login", "/api/v1/auth/login/", {"email": "x@example.com", "password": "wrong"}),
        ("auth_verify", "/api/v1/auth/verify-email/", {"email": "x@example.com", "otp": "000000"}),
        ("auth_resend", "/api/v1/auth/resend-verification/", {"email": "x@example.com"}),
        ("auth_password_reset_request", "/api/v1/auth/password-reset/", {"email": "x@example.com"}),
        ("auth_password_reset_confirm", "/api/v1/auth/password-reset/confirm/", {"email": "x@example.com", "otp": "000000", "password": "NewSecurePass123!"}),
        ("auth_refresh", "/api/v1/auth/refresh/", {}),
    ]

    @pytest.mark.parametrize("scope,url,payload", CASES, ids=[c[0] for c in CASES])
    def test_third_request_is_throttled(self, api_client, scope, url, payload):
        responses = [
            api_client.post(url, payload, format="json") for _ in range(3)
        ]

        # First two requests pass through throttling (may fail validation — that's fine,
        # throttle counting happens before the handler runs).
        assert responses[0].status_code != 429
        assert responses[1].status_code != 429
        # Third request exceeds the 2/min scoped limit.
        assert responses[2].status_code == 429

    def test_throttled_response_uses_error_envelope(self, api_client):
        for _ in range(2):
            api_client.post("/api/v1/auth/login/", {"email": "x@example.com", "password": "w"}, format="json")
        response = api_client.post("/api/v1/auth/login/", {"email": "x@example.com", "password": "w"}, format="json")

        assert response.status_code == 429
        body = response.json()
        assert body["status"] == "error"
        assert body["code"] == "RATE_LIMIT_EXCEEDED"
        assert "message" in body
        assert "fields" in body

    def test_throttled_response_includes_retry_after(self, api_client):
        for _ in range(2):
            api_client.post("/api/v1/auth/login/", {"email": "x@example.com", "password": "w"}, format="json")
        response = api_client.post("/api/v1/auth/login/", {"email": "x@example.com", "password": "w"}, format="json")

        assert response.status_code == 429
        assert "Retry-After" in response
        assert int(response["Retry-After"]) >= 0


@pytest.mark.django_db
class TestGlobalAnonThrottle:
    """Unauthenticated traffic to non-scoped DRF endpoints hits the global anon throttle."""

    @pytest.fixture(autouse=True)
    def tight_anon_throttle(self):
        with override_settings(REST_FRAMEWORK=_TIGHT_ANON):
            yield

    def test_third_request_is_throttled(self, api_client):
        responses = [api_client.get("/api/schema/") for _ in range(3)]

        assert responses[0].status_code != 429
        assert responses[1].status_code != 429
        assert responses[2].status_code == 429


@pytest.mark.django_db
class TestGlobalUserThrottle:
    """Authenticated traffic hits the global per-user throttle."""

    @pytest.fixture(autouse=True)
    def tight_user_throttle(self):
        with override_settings(REST_FRAMEWORK=_TIGHT_USER):
            yield

    def test_third_request_is_throttled(self, api_client, verified_user):
        api_client.force_authenticate(user=verified_user)

        responses = [api_client.get("/api/v1/auth/profile/") for _ in range(3)]

        assert responses[0].status_code == 200
        assert responses[1].status_code == 200
        assert responses[2].status_code == 429


@pytest.mark.django_db
class TestHappyPathUnaffected:
    """Default (test) rates must not break normal single-request flows."""

    def test_single_login_succeeds(self, api_client, verified_user):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": verified_user.email, "password": "SecurePass123!"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"


@pytest.mark.django_db
class TestPasswordResetCooldown:
    """Service-level 60s resend cooldown on password-reset (silent, anti-enumeration)."""

    @mock.patch("apps.notifications.tasks.send_password_reset_email_task")
    def test_second_request_within_cooldown_does_not_dispatch(self, mock_task, verified_user):
        email = verified_user.email.lower()

        first = AccountsService.request_password_reset(verified_user.email)
        assert first is True
        mock_task.delay.assert_called_once()
        record_after_first = cache.get(f"{PASSWORD_RESET_CACHE_PREFIX}{email}")
        assert record_after_first is not None
        assert cache.get(f"{PASSWORD_RESET_COOLDOWN_PREFIX}{email}") is not None

        second = AccountsService.request_password_reset(verified_user.email)
        assert second is True  # still returns success — no enumeration signal
        mock_task.delay.assert_called_once()  # but no email dispatched
        assert cache.get(f"{PASSWORD_RESET_CACHE_PREFIX}{email}") == record_after_first  # no new OTP issued

    @mock.patch("apps.notifications.tasks.send_password_reset_email_task")
    def test_request_after_cooldown_expires_dispatches_again(self, mock_task, verified_user):
        email = verified_user.email.lower()

        AccountsService.request_password_reset(verified_user.email)
        assert mock_task.delay.call_count == 1

        # Simulate cooldown expiry
        cache.delete(f"{PASSWORD_RESET_COOLDOWN_PREFIX}{email}")

        AccountsService.request_password_reset(verified_user.email)
        assert mock_task.delay.call_count == 2

    @mock.patch("apps.notifications.tasks.send_password_reset_email_task")
    def test_unknown_email_returns_true_without_dispatch_or_cooldown(self, mock_task):
        result = AccountsService.request_password_reset("nobody@example.com")

        assert result is True
        mock_task.delay.assert_not_called()
        assert cache.get(f"{PASSWORD_RESET_COOLDOWN_PREFIX}nobody@example.com") is None
