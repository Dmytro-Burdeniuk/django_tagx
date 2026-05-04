import os

from config.env import BASE_DIR, env

env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env.str("SECRET_KEY")

DEBUG = env.bool("DJANGO_DEBUG", default=True)

ALLOWED_HOSTS = ["*"]

INTERNAL_IPS = [
    "127.0.0.1",
]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": "config.debug.show_toolbar",
}

INSTALLED_APPS = [
    "django.contrib.gis",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # django libraries
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "debug_toolbar",
    "storages",
    # local apps
    "apps.users",
    "apps.authentication",
    "apps.graffiti",
]

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "EXCEPTION_HANDLER": "core.exception_handler.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Postgres Config
from config.settings.postgres import *  # noqa

# JWT Config
from config.settings.jwt import *  # noqa

# S3 Storage Configuration
USE_S3 = env.bool("USE_S3", default=False)

if USE_S3:
    # AWS S3 settings
    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")
    AWS_S3_CUSTOM_DOMAIN = env.str("AWS_S3_CUSTOM_DOMAIN", default=None)
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

    # S3 static settings
    STATIC_LOCATION = "static"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/" if AWS_S3_CUSTOM_DOMAIN else f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{STATIC_LOCATION}/"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    # S3 media settings
    MEDIA_LOCATION = "media"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIA_LOCATION}/" if AWS_S3_CUSTOM_DOMAIN else f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{MEDIA_LOCATION}/"
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
else:
    # Local file storage
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ===========================
# SPECTACULAR (API DOCUMENTATION)
# ===========================
SPECTACULAR_SETTINGS = {
    'TITLE': 'Graffiti Map API',
    'DESCRIPTION': 'MVP API for graffiti mapping and voting',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
}
