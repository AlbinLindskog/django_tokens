import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'totally_not-secret-tests'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = []

MIDDLEWARE = []

TEMPLATES = []

WSGI_APPLICATION = 'tests.wsgi.application'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'default'
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}