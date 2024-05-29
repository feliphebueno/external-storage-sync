import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = environ.Path(__file__) - 2
APPS_DIR = BASE_DIR.path("app")


# Environment variables
env = environ.Env()
env.read_env(f"{BASE_DIR}/.env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        "django-external-storage-sync",
    ],
)


# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "django_dramatiq",
]

LOCAL_APPS = [
    "app.sync.apps.SyncConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "app.sync.middleware.HMacAuthenticationMiddleware",
    "app.sync.middleware.JSONParseValidationMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Cache
# https://docs.djangoproject.com/en/5.0/topics/cache/

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": env.str("MEMCACHED_URL"),
    },
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_ROOT = str(APPS_DIR.path("staticfiles"))
STATIC_URL = env.str("DJANGO_STATIC_URL", default="/static/")
STATICFILES_DIRS = [APPS_DIR.path("static").root]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MEDIA_ROOT = env.str("DJANGO_MEDIA_ROOT", default=BASE_DIR.path("storage/"))
MEDIA_URL = env.str("DJANGO_MEDIA_URL", default="/media/")

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Apps MISC
# 1 hour in seconds
STATS_CACHE_TIMEOUT = 3_600

# 2 minutes in milliseconds
SYNC_S3_TASK_TIME_LIMIT = 60_000

STORAGE_PATH = env.str("STORAGE_PATH")

# 3rd party settings
DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.rabbitmq.RabbitmqBroker",
    "OPTIONS": {
        "url": env.str("RABBITMQ_URL"),
    },
    "MIDDLEWARE": [
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "dramatiq.middleware.CurrentMessage",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ],
}

NASA_API_URL = env.url("NASA_API_URL").geturl()
NASA_API_KEY = env.str("NASA_API_KEY")

# Half an hour in seconds
NASA_REQUEST_CACHE_TIMEOUT = 1_800

# DISCLAIMER: Won't be used on this demo project
AWS_CREDENTIALS = {
    "aws_access_key_id": env.str("AWS_S3_ACCESS_KEY_ID"),
    "aws_secret_access_key": env.str("AWS_S3_SECRET_ACCESS_KEY"),
    "region_name": env.str("AWS_S3_REGION_NAME"),
    "bucket_name": env.str("AWS_S3_BUCKET_NAME"),
}

# Django Ratelimit blocked view
RATELIMIT_VIEW = "app.sync.views.rate_limited_error_view"

# DEBUG OVERRIDES
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    from .debug_settings import *  # noqa
