"""
Docker / Compose settings.
Postgres-backed, WhiteNoise static files, SSL relaxed for local containers.
"""
from .base import *  # noqa: F401,F403

DEBUG = env.bool('DJANGO_DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

SECRET_KEY = env(
    'SECRET_KEY',
    default='docker-compose-dev-secret-change-me-before-prod-use'
)

DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default='postgres://purohit:purohit@db:5432/purohitconnect'
    )
}

# Local containers usually terminate TLS at a proxy (or not at all)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)

CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=['http://localhost:8010', 'http://127.0.0.1:8010']
)

# WhiteNoise is already enabled in base MIDDLEWARE
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)

TWILIO_ALLOW_MOCK = env.bool('TWILIO_ALLOW_MOCK', default=True)

REDIS_URL = env('REDIS_URL', default=None)
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
