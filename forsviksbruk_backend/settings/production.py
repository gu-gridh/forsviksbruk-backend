from .base import *
import os
from django.core.exceptions import ImproperlyConfigured

DEBUG = False

# Refuse to start with a missing or default secret key
if SECRET_KEY == INSECURE_SECRET_KEY:
    raise ImproperlyConfigured("Set SECRET_KEY in the environment for production.")

# Default static storage: ManifestStaticFilesStorage fails on collectstatic because
# third-party admin assets reference missing source maps (e.g. js/wNumb.min.js.map)

# Additional production settings
# Set SECURE_SSL_REDIRECT=False if the reverse proxy already redirects to https
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Email
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '25'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
