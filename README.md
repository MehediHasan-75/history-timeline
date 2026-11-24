# History Timeline

Django application for recording and exploring historical and literary events across BCE and CE. Historical dates use signed integer components instead of database date fields, so ancient dates remain representable.

The application includes bilingual English/Bangla UI, Gregorian and Bangladesh revised Bengali calendar input, event CRUD, privacy controls, TimelineJS feeds, and production deployment configuration.

## Pinned stack

- Python 3.12
- Django 6.1.1
- PostgreSQL 15 or newer; local Compose uses PostgreSQL 17
- psycopg 3.3.9
- Gunicorn 27.0.1
- WhiteNoise 6.12.0
- Tailwind CSS 3.4.17
- TimelineJS 3.9.13
- Node.js 22 and npm 10

## Local setup

### 1. Create the Python environment

Ubuntu/Debian users may need `python3.12-venv` before creating the environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.in` lists direct dependencies. `requirements.txt` pins the complete resolved environment for reproducible installs.

### 2. Configure environment variables

```bash
cp .env.example .env
```

Replace `DJANGO_SECRET_KEY` before using any non-local environment. Development defaults expect PostgreSQL at `127.0.0.1:5432` with database, user, and password all named `history`.

### 3. Start PostgreSQL

With Docker Compose:

```bash
docker compose up -d db
docker compose ps
```

Or create the database in an existing PostgreSQL 15+ server:

```bash
createuser --createdb --pwprompt history
createdb --owner=history history
```

The database must use UTF-8. SQLite is intentionally unsupported.

### 4. Install and build frontend assets

```bash
npm install
npm run build
```

For active development, run these in separate terminals:

```bash
npm run watch:css
npm run watch:js
```

### 5. Initialize and run Django

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. The database-aware health endpoint is `http://127.0.0.1:8000/health/`.

## Checks

Run the verification suite:

```bash
source .venv/bin/activate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
npm test
npm run build
```

`python manage.py test` uses mocked database access only for the health endpoint during Phase 1. Running migrations and the live health check requires PostgreSQL.

## Settings

- Development: `config.settings.development`
- Production: `config.settings.production`

`manage.py` defaults to development. WSGI and ASGI default to production, where a real secret key and allowed hosts are mandatory.

Required production environment variables:

- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`

Optional production variables:

- `DJANGO_SECURE_SSL_REDIRECT`, default `True`
- `DJANGO_SECURE_HSTS_SECONDS`, default `31536000`
- `DJANGO_DB_CONN_MAX_AGE`, default `60`

Example production commands:

```bash
npm ci
npm run build
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Project layout

```text
accounts/          Authentication and profile application
assets/            Tailwind and JavaScript source
config/            URLs, WSGI/ASGI, and split settings
core/              Landing, dashboard shell, and health checks
events/            Event domain application
static/dist/       Compiled frontend assets
templates/         Project-level Django templates
tests/             Frontend contract tests
```

See `project_blueprint.md` for product and phase requirements. See `UI_INTEGRATION.md` for template context and JSON contracts.

## Bengali calendar

Each start and end date independently selects Gregorian or Bangladesh Bengali calendar. Bengali digits (`০–৯`) and Western digits (`0–9`) are accepted. Current Bangladesh revised rules apply proleptically. A year-only Bengali date is stored with inclusive Gregorian bounds; for example, `১৩৭০ বঙ্গাব্দ` maps to `1963-04-14` through `1964-04-13`. Original Bengali components remain available for editing and localized display.

Create repeatable demonstration content after migrations:

```bash
python manage.py seed_demo
```

## Free Render + Neon deployment

1. Push this repository to GitHub and create a free Neon PostgreSQL project.
2. In Render, create a Blueprint from `render.yaml`.
3. Set `DATABASE_URL` to Neon pooled connection string with `sslmode=require`.
4. Set `DJANGO_ALLOWED_HOSTS` to the Render hostname, such as `history-timeline.onrender.com`.
5. Set `DJANGO_CSRF_TRUSTED_ORIGINS` to the HTTPS origin, such as `https://history-timeline.onrender.com`.
6. For initial admin creation only, set `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, and `DJANGO_SUPERUSER_PASSWORD`. Remove all three after successful startup.
7. Verify `/health/live/`, `/health/ready/`, registration, admin, event CRUD, language switching, and public/private feeds.

Render runs `scripts/build.sh`, then `scripts/start.sh`. Startup applies migrations before Gunicorn starts. Back up Neon before migrations. Roll back by restoring the database backup and deploying a compatible prior commit. Test restores in a separate Neon branch before relying on them.

### Optional keepalive

GitHub Actions can call the shallow live endpoint every 10 minutes. Add repository secret `APP_HEALTH_URL` containing the Render origin and repository variable `ENABLE_KEEPALIVE=true`. The workflow runs `scripts/keepalive.sh`. A sleeping service cannot wake itself, so the external runner is required. Free services can still restart or exhaust provider limits; this is not an uptime guarantee.

### Operations

- Application logs go to stdout/stderr and appear in Render logs.
- `/health/live/` checks the web process without querying Neon.
- `/health/ready/` and `/health/` verify PostgreSQL connectivity.
- Static files use WhiteNoise compressed manifest storage.
- Local filesystem data is ephemeral in Render; store durable application data only in PostgreSQL.
- Upgrade hosting before treating the service as availability-sensitive production.
