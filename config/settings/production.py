from .base import *

# Production settings
DEBUG = False

# Security configurations
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Add production-specific database setup here (e.g. Postgres) if configured
# DATABASES['default'] = dj_database_url.config(...)
