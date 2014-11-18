import os

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/"

DATABASES  = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME"  : os.path.join(PROJECT_PATH, "data.sqlite"),
        "OPTIONS": {
            "timeout": 60,
        },
    }
}

INTERNAL_IPS   = ("127.0.0.1",)
ALLOWED_HOSTS = ['*']

TIME_ZONE = None

LANGUAGE_CODE  = "en"
USE_I18N = True
USE_L10N = False

SECRET_KEY = "notsosecret"

ROOT_URLCONF = "flexmodels.demo.urls"

INSTALLED_APPS = (
    "django.contrib.admin", # this and the following are needed to enable django admin.
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django_extensions", # needed for clean_pyc (testing)
    "flexmodels",
    "flexmodels.demo",
)

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.realpath(PROJECT_PATH + "/media/") + "/"
STATIC_URL = "/static/"
STATIC_ROOT = os.path.realpath(PROJECT_PATH + "/static/") + "/"

DEFAULT_ENCODING = 'utf-8'

DEBUG = True