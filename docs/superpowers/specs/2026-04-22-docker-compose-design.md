# Docker Compose Infrastructure Design

**Date:** 2026-04-22  
**Project:** django-template  
**Status:** Approved

---

## Goal

Організувати Docker-інфраструктуру для production-ready Django template таким чином, щоб:
- Усі можливі сервіси були присутні в шаблоні
- Сервіси можна вмикати/вимикати через Docker Compose profiles
- Не було дублювання Dockerfile між середовищами
- Структура була зрозумілою для нових проектів, що використовують цей template

---

## Chosen Approach

**Per-env папки + Docker Compose profiles.**

Один `Dockerfile` з multi-stage builds, окремі start-скрипти per-env/per-service, profiles для опціональних сервісів.

---

## File Structure

```
django_template/
├── Dockerfile                          # один multi-stage файл для всіх середовищ
├── docker-compose.local.yml            # local dev stack
├── docker-compose.production.yml       # production stack
│
└── compose/
    ├── local/
    │   ├── django/
    │   │   └── start                   # uvicorn --reload
    │   ├── celery/
    │   │   ├── worker/start            # celery worker
    │   │   ├── beat/start              # celery beat
    │   │   └── flower/start            # flower UI
    │   └── postgres/
    │       └── init.sql                # ініціалізація БД (опційно)
    │
    └── production/
        ├── django/
        │   └── start                   # gunicorn
        ├── celery/
        │   ├── worker/start
        │   ├── beat/start
        │   └── flower/start
        └── nginx/
            └── nginx.conf
```

---

## Dockerfile (multi-stage)

Три stages:

| Stage | Базується на | Призначення |
|-------|-------------|-------------|
| `base` | python:3.12-slim | Спільні системні залежності, uv, копіює pyproject.toml |
| `dev` | base | Додає dev + test групи залежностей, налаштований для розробки |
| `prod` | base | Тільки production залежності, non-root user, мінімальний образ |

- `docker-compose.local.yml` → `--target dev`
- `docker-compose.production.yml` → `--target prod`

---

## Docker Compose Profiles

### Local (`docker-compose.local.yml`)

| Сервіс | Profile | Завжди активний |
|--------|---------|----------------|
| `django` | — | ✓ |
| `postgres` | — | ✓ |
| `redis` | `redis` | |
| `celery-worker` | `celery` | |
| `celery-beat` | `celery` | |
| `flower` | `flower` | |

> `flower` потребує активного `celery` профілю для коректної роботи.

### Production (`docker-compose.production.yml`)

| Сервіс | Profile | Завжди активний |
|--------|---------|----------------|
| `django` | — | ✓ |
| `postgres` | — | ✓ |
| `redis` | `redis` | |
| `nginx` | `nginx` | |
| `celery-worker` | `celery` | |
| `celery-beat` | `celery` | |
| `flower` | `flower` | |

### Приклади запуску (local)

```bash
# django + postgres (дефолт)
docker compose -f docker-compose.local.yml up

# + redis
docker compose -f docker-compose.local.yml --profile redis up

# + redis + celery
docker compose -f docker-compose.local.yml --profile redis --profile celery up

# + redis + celery + flower
docker compose -f docker-compose.local.yml --profile redis --profile celery --profile flower up
```

---

## Start Scripts

Кожен start-скрипт — bash-файл з `set -o errexit / pipefail / nounset`.

| Скрипт | Що робить |
|--------|-----------|
| `local/django/start` | `wait_for_db` → `migrate` → `collectstatic` → `uvicorn --reload` |
| `production/django/start` | `wait_for_db` → `migrate` → `collectstatic` → `gunicorn` |
| `*/celery/worker/start` | `wait_for_db` → `celery worker` |
| `*/celery/beat/start` | `wait_for_db` → `celery beat` |
| `*/celery/flower/start` | `celery flower` |

`wait_for_db` — кастомна Django management command, яка чекає поки PostgreSQL стане доступним.

---

## Environment Variables

`.env.example` розширюється до:

```dotenv
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://postgres:postgres@postgres:5432/django_template

# Cache
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## Scope

**В цьому дизайні:**
- Структура файлів та папок
- Dockerfile multi-stage strategy
- Docker Compose profiles для всіх сервісів
- Start-скрипти per-service per-env
- Оновлення `.env.example`
- Оновлення `justfile` для нових команд
- Додавання Python-залежностей до `pyproject.toml`: `uvicorn`, `gunicorn`, `celery`, `redis`, `django-celery-beat`, `flower`, `psycopg[binary]`, `django-redis`
- `wait_for_db` management command

**Поза scope:**
- CI/CD pipeline конфігурація
- Kubernetes / production deployment
- SSL сертифікати (nginx конфіг — базовий)
- Моніторинг (Prometheus, Grafana)
