# SafeAlert Web Deployment

## Required environment variables

Set these on the hosting provider:

```env
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
ALLOWED_HOSTS=your-backend-domain.com
DATABASE_URL=postgres://user:password@host:5432/database
DATABASE_SSL_REQUIRE=True
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
CSRF_TRUSTED_ORIGINS=https://your-backend-domain.com
SECURE_SSL_REDIRECT=True
```

For a mobile-only APK, `CORS_ALLOWED_ORIGINS` is less important than it is for browsers, but keep it configured for the web dashboard/admin pages.

## Build command

```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

## Start command

```bash
gunicorn config.wsgi:application
```

## After first deploy

Create an admin user:

```bash
python manage.py createsuperuser
```

Then add at least one `Building` from the web admin/dashboard. The mobile registration screen needs `/api/buildings/` to return building data.

## Mobile APK API URL

Build the Flutter APK with the deployed API URL:

```bash
flutter build apk --release --dart-define=SAFEALERT_API_URL=https://your-backend-domain.com/api
```
