from .base import *

DEBUG = env.bool('DJANGO_DEBUG', default=True)

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database (SQLite for local dev fallback, PostgreSQL is better)
# The implementation plan mentioned PostgreSQL, so we'll configure it to use that by default if provided, otherwise fallback to SQLite
DATABASES = {
    'default': env.db('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# Static files mapping for dev
STATIC_URL = 'static/'
MEDIA_URL = 'media/'

# Email Configuration (Console backend for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@purohitconnect.local'

# For production, configure SMTP:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'  # or your email provider
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'
