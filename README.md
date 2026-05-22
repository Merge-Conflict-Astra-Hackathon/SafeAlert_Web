# SafeAlert Web

Dashboard web SafeAlert untuk operator memverifikasi user, mengelola gedung, melihat status evakuasi, dan mengirim alarm darurat ke aplikasi mobile.

## Link Deploy

- Web production: https://safealertweb-production.up.railway.app/
- Bitrise: https://safealertweb-production.up.railway.app/

Catatan: link Bitrise di atas masih sama dengan link production yang diberikan. Ganti dengan URL Bitrise asli jika pipeline sudah tersedia.

## Stack

- Django 4.2
- Django REST Framework
- Simple JWT
- PostgreSQL Railway
- Firebase Admin SDK untuk FCM
- WhiteNoise untuk static files

## Environment Railway

Set variable berikut di Railway:

```env
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=safealert-random-secret-yang-panjang-banget
DEBUG=True
ALLOWED_HOSTS=safealertweb-production.up.railway.app
DATABASE_URL=${{Postgres.DATABASE_URL}}
DATABASE_SSL_REQUIRE=True
SECURE_SSL_REDIRECT=False
CSRF_TRUSTED_ORIGINS=https://safealertweb-production.up.railway.app
CORS_ALLOWED_ORIGINS=https://safealertweb-production.up.railway.app
NIXPACKS_PYTHON_VERSION=3.12
FIREBASE_CREDENTIALS_JSON=<service-account-json>
```

## Railway Commands

Build Command boleh dikosongkan. Jika ingin collect static saat deploy:

```bash
python manage.py collectstatic --noinput
```

Start Command:

```bash
python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Jangan isi command Flutter seperti `--release --dart-define=...` di Railway. Parameter itu hanya untuk build APK di Bitrise.

## Local Development

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Dashboard lokal:

```text
http://127.0.0.1:8000/dashboard/
```

## Deploy Flow

1. Commit perubahan ke branch `main`.
2. Push ke GitHub.
3. Railway auto deploy dari branch `main`.
4. Jika auto deploy tidak berjalan, buka Railway lalu klik **Redeploy** pada service web.
