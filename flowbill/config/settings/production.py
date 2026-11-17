from .base import *
from decouple import config

DEBUG = False
EXPOSE_API_DOCS = config("EXPOSE_API_DOCS", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")])

# ─── DRF throttling identity behind the reverse proxy ────────────────────────
# DRF derives the throttle key from X-Forwarded-For only when NUM_PROXIES is
# set. Behind Render's single proxy hop, unset NUM_PROXIES would bucket ALL
# users on the proxy IP (mass false 429s); the value must match the real
# number of trusted proxies so the header cannot be spoofed for fresh buckets.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "NUM_PROXIES": config("NUM_PROXIES", cast=int, default=1),
}

# ─── Database ────────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 10,
            "sslmode": "require",
        },
    }
}

# ─── Cache & Celery ──────────────────────────────────────────────────────────
REDIS_URL = config("REDIS_URL")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# ─── CORS ────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    cast=lambda v: [s.strip() for s in v.split(",")]
)
CORS_ALLOW_CREDENTIALS = True

# ─── Email ───────────────────────────────────────────────────────────────────
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="FlowBill <noreply@flowbill.app>")

ANYMAIL = {
    "MAILGUN_API_KEY": config("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": config("MAILGUN_SENDER_DOMAIN"),
}

# ─── Security headers ────────────────────────────────────────────────────────
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ─── Static files (WhiteNoise for Render) ────────────────────────────────────
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ─── Logging — JSON only in production ───────────────────────────────────────
LOGGING["root"]["handlers"] = ["json_file"]
LOGGING["loggers"]["django"]["handlers"] = ["json_file"]