"""
Django settings for DSTBundesliga project.

Generated by 'django-admin startproject' using Django 3.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import datetime

from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['dstffbl.uber.space', '.downsettalk.de']

SITE_ID = 1

# Application definition

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'patreon': {
        'VERSION': 'v2',
        'SCOPE': ['identity', 'identity[email]', 'identity.memberships']
    }
}

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
SOCIALACCOUNT_ADAPTER = "DSTBundesliga.apps.dstffbl.models.CustomSocialAccountAdapter"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION ='none'
SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_NAME = 'dstffbl_session_id'


INSTALLED_APPS = [
    'djangocms_admin_style',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',

    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'cms',
    'menus',
    'treebeard',
    'sekizai',
    'filer',
    'easy_thumbnails',
    'mptt',
    'djangocms_text_ckeditor',
    'djangocms_link',
    'djangocms_file',
    'djangocms_picture',
    'djangocms_video',
    'djangocms_googlemap',
    'djangocms_snippet',
    'djangocms_style',
    'django_tables2',
    'cookielaw',
    'tinymce',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.patreon',
    'DSTBundesliga.apps.leagues',
    'DSTBundesliga.apps.dstffbl',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
]

ROOT_URLCONF = 'DSTBundesliga.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'sekizai.context_processors.sekizai',
                'cms.context_processors.cms_settings',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'DSTBundesliga.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGES = [
    ('en', 'English'),
    ('de', 'German'),
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CMS_TEMPLATES = [
    ('home.html', 'Home page template'),
]

CMS_PERMISSION = True

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.expanduser("~/html/media/")

THUMBNAIL_HIGH_RESOLUTION = True

THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
    'easy_thumbnails.processors.filters'
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.expanduser("~/html/static/")
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'staticfiles')]
ADMIN_MEDIA_PREFIX = "/static/admin/"

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

if os.getenv('DEV', 0) == '1':
    from local_settings import *

    STATIC_ROOT = os.path.join(BASE_DIR, "static/")
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'mydatabase',
        }
    }
else:
    # Database
    # https://docs.djangoproject.com/en/3.0/ref/settings/#databases

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'OPTIONS': {
                'read_default_file': os.getenv('DB_OPTIONS_FILE'),
            },
        }
    }

import hashlib
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


CSS_VERSION_HASH = md5(os.path.join(BASE_DIR, "staticfiles/css/base.css"))
REGISTRATION_OPEN = os.getenv('REGISTRATION_OPEN', 0) == '1'

DEFAULT_LEAGUE_SETTINGS_PATH = os.path.join(BASE_DIR, "Ligaübersicht.csv")

DEFAULT_NEWS_LOGO = "dst_logo_96.png"

RSS_FEED = "https://anchor.fm/s/1ce78cc4/podcast/rss"
PODCAST_NEWS_LOGO = "podcast.jpg"
RSS_TIMESTAMP_FILE = ".rss_ts"

LISTENER_LEAGUE_ID = "603961066644373504"

SCHEDULE = {
    1: datetime.datetime(2020, 9, 11),
    2: datetime.datetime(2020, 9, 18),
    3: datetime.datetime(2020, 9, 25),
    4: datetime.datetime(2020, 10, 2),
    5: datetime.datetime(2020, 10, 9),
    6: datetime.datetime(2020, 10, 16),
    7: datetime.datetime(2020, 10, 23),
    8: datetime.datetime(2020, 10, 30),
    9: datetime.datetime(2020, 11, 6),
    10: datetime.datetime(2020, 11, 13),
    11: datetime.datetime(2020, 11, 20),
    12: datetime.datetime(2020, 11, 27),
    13: datetime.datetime(2020, 12, 4),
    14: datetime.datetime(2020, 12, 11),
    15: datetime.datetime(2020, 12, 18),
    16: datetime.datetime(2020, 12, 25),
    17: datetime.datetime(2021, 1, 3)
}

DST_PATREON_CAMPAIGN_ID = '2708731'


