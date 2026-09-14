from pathlib import Path
import os
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-mvp-secret-key-change-in-prod')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'django_filters',
    'django_htmx',
    'imagekit',
    'django_extensions',
    
    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.purohits',
    'apps.pujas',
    'apps.bookings',
    'apps.reviews',
    'apps.dashboard',
    'apps.api',
]

MIDDLEWARE = [
    'apps.api.middleware.MobileApiCorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.global_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Twilio SMS / WhatsApp Configuration
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default=None)
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default=None)
TWILIO_FROM_NUMBER = env('TWILIO_FROM_NUMBER', default=None)
# WhatsApp sender in E.164 (e.g. +14155238886 for Twilio sandbox) or full "whatsapp:+...."
TWILIO_WHATSAPP_FROM = env('TWILIO_WHATSAPP_FROM', default=None)
# Allow console mock SMS/WhatsApp when Twilio is not configured (dev only)
TWILIO_ALLOW_MOCK = env.bool('TWILIO_ALLOW_MOCK', default=True)

# Razorpay Settings
RAZORPAY_KEY_ID = env('RAZORPAY_KEY_ID', default='rzp_test_YOUR_KEY_HERE')
RAZORPAY_KEY_SECRET = env('RAZORPAY_KEY_SECRET', default='YOUR_SECRET_HERE')
RAZORPAY_CURRENCY = 'INR'
RAZORPAY_WEBHOOK_SECRET = env('RAZORPAY_WEBHOOK_SECRET', default=None)
# Allow local mock checkout when Razorpay keys are missing/placeholder (dev only)
RAZORPAY_ALLOW_MOCK = env.bool('RAZORPAY_ALLOW_MOCK', default=True)
# Flutter web origins allowed to call /api/v1/. Empty in production unless set.
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
# RazorpayX current account number used as source for payouts
RAZORPAYX_ACCOUNT_NUMBER = env('RAZORPAYX_ACCOUNT_NUMBER', default=None)
RAZORPAYX_PAYOUT_MODE = env('RAZORPAYX_PAYOUT_MODE', default='IMPS')
# Withdrawals require admin-verified bank details by default
WITHDRAWAL_REQUIRE_VERIFIED_BANK = env.bool('WITHDRAWAL_REQUIRE_VERIFIED_BANK', default=True)
# Auto-send RazorpayX payout without admin approval (only if bank verified when required)
WITHDRAWAL_AUTO_PAYOUT = env.bool('WITHDRAWAL_AUTO_PAYOUT', default=False)

# Reschedule policy
RESCHEDULE_MAX_COUNT = env.int('RESCHEDULE_MAX_COUNT', default=2)
RESCHEDULE_MIN_NOTICE_HOURS = env.int('RESCHEDULE_MIN_NOTICE_HOURS', default=48)
RESCHEDULE_PENDING_EXPIRE_HOURS = env.int('RESCHEDULE_PENDING_EXPIRE_HOURS', default=24)
