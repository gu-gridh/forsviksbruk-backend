from .base import *
import os

DEBUG = False

MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(BASE_DIR, "media"))
MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
STATIC_ROOT = os.getenv("STATIC_ROOT", os.path.join(BASE_DIR, "static"))
STATIC_URL = os.getenv("STATIC_URL", "/static/")

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache.
# See https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
if "STORAGES" not in globals():
	STORAGES = {}
STORAGES.setdefault("staticfiles", {})
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"



ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'your-domain.com,www.your-domain.com').split(',')
CSRF_TRUSTED_ORIGINS = ["https://your-domain.com"]

# Additional production settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASS'),
        'HOST': os.getenv('HOST'),
        'PORT': os.getenv('PORT'),
    }
}
