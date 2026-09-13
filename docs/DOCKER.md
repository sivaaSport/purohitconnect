# Docker / Compose

## Prerequisites
- Docker Desktop (Windows/macOS) or Docker Engine + Compose plugin

## Quick start
```bash
# from project root
docker compose up --build
```

App: http://localhost:8010/  
(host port is `WEB_PORT`, default `8010`, so it does not clash with other apps on `8000`)
Postgres: `localhost:5432` (user/pass/db: `purohit` / `purohit` / `purohitconnect`)

On first start the container:
1. waits for Postgres
2. runs migrations
3. collects static files
4. seeds cities/languages (`SEED_ON_START=1`)
5. starts Gunicorn

## Useful commands
```bash
docker compose up --build -d
docker compose logs -f web
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_db
docker compose down
# wipe DB volume too:
docker compose down -v
```

## Optional Redis
```bash
REDIS_URL=redis://redis:6379/1 docker compose --profile redis up --build
```

## Files
- `Dockerfile` — app image
- `docker-compose.yml` — web + Postgres (+ optional Redis)
- `.env.docker` — container env (gitignored pattern; example committed as `.env.docker`)
- `config/settings/docker.py` — compose-friendly Django settings
- `scripts/docker-entrypoint.sh` — migrate/collectstatic before boot

## Production note
For a real host, use `config.settings.production`, strong `SECRET_KEY`, live DB credentials, TLS, and do **not** ship default `purohit/purohit` passwords.
