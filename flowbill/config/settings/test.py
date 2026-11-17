from .development import *

# Use in-memory cache — no Redis needed for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Neutralize throttle rates so the existing suite never trips them, while
# keeping the throttling machinery exercised. Throttling behaviour itself is
# tested in apps/accounts/tests/test_throttling.py via override_settings.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        k: "1000/sec" for k in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    },
}

# Faster password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Synchronous Celery — no broker needed
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True