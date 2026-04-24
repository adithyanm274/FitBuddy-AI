"""
Django settings for my_website project.
Adapted for local development – falls back to SQLite and local-friendly defaults.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------
# Environment detection – set `DJANGO_ENV=production` on Render
# ------------------------------------------------------------------
ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY and ENVIRONMENT == 'production':
    raise ValueError("DJANGO_SECRET_KEY must be set in production")
if not SECRET_KEY:
    # Generate a simple default for local use (never use in production)
    SECRET_KEY = 'django-insecure-local-dev-key-do-not-use-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True' if ENVIRONMENT == 'development' else 'False') == 'True'

# Allowed hosts – add your local IP if needed
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
if ENVIRONMENT == 'production':
    ALLOWED_HOSTS.append('fitbuddy-ai-ruap.onrender.com')

# Application definition
INSTALLED_APPS = [
    'user_module',
    'admin_module',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',   # still useful locally, but not critical
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'my_website.urls'

# ------------------------------------------------------------------
# Caching – use local memory cache for development
# ------------------------------------------------------------------
if ENVIRONMENT == 'production':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache_table',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'my_website.wsgi.application'

# ------------------------------------------------------------------
# DATABASE – use PostgreSQL only if DATABASE_URL is set, else SQLite
# ------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'fitbuddy_db',  # Make sure this matches your database name
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# For local development, use simple static storage (no manifest hashing)
if ENVIRONMENT == 'production':
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------------------------------------------
# AI API key – always required (set in .env file for local)
# ------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY','AIzaSyAempffoDr6LdL3dL3S9jPFaJigSRuKxlc')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Create a .env file with GEMINI_API_KEY=your_key")

# ------------------------------------------------------------------
# Security settings – relax for local development, enforce for production
# ------------------------------------------------------------------
if ENVIRONMENT == 'production':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
else:
    # Local development (HTTP only)
    SECURE_PROXY_SSL_HEADER = None
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False