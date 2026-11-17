from django.apps import AppConfig
from django.core.signals import setting_changed


def _sync_drf_throttle_rates(sender, setting, **kwargs):
    """
    DRF binds `SimpleRateThrottle.THROTTLE_RATES` at class definition time, so
    `override_settings(REST_FRAMEWORK=...)` reloads `api_settings` without
    updating `SimpleRateThrottle.THROTTLE_RATES`. Keep it in sync whenever
    `REST_FRAMEWORK` changes.
    """
    if setting == "REST_FRAMEWORK":
        from rest_framework.settings import api_settings
        from rest_framework.throttling import SimpleRateThrottle

        SimpleRateThrottle.THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    label = "core"

    def ready(self):
        setting_changed.connect(
            _sync_drf_throttle_rates,
            dispatch_uid="core.sync_drf_throttle_rates",
        )
