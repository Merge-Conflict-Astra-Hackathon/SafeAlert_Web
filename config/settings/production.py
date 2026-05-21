from .base import *
import dj_database_url

# Production settings
DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())
railway_public_domain = config('RAILWAY_PUBLIC_DOMAIN', default='')
if railway_public_domain and railway_public_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(railway_public_domain)
if '.up.railway.app' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.up.railway.app')

database_url = config('DATABASE_URL', default='')
if database_url:
    DATABASES['default'] = dj_database_url.parse(
        database_url,
        conn_max_age=600,
        ssl_require=config('DATABASE_SSL_REQUIRE', default=True, cast=bool),
    )

# Security configurations
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
