"""Isolated test configuration: no dotenv, credentials, or external services.

Run from this directory with:
    python -m django test explore --settings=test_settings
"""

SECRET_KEY = 'test-only-not-for-deployment'
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'users',
    'media',
    'explore',
]
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
AUTH_USER_MODEL = 'users.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
ROOT_URLCONF = __name__
urlpatterns = []
