# Django Template - Universal Commands
# Usage: just help

@help:
    echo "🚀 Django Project - Available Commands"
    echo ""
    echo "Setup:"
    echo "  just install          Install all dependencies"
    echo "  just sync             Sync dependencies"
    echo ""
    echo "Development:"
    echo "  just run              Run development server"
    echo "  just shell            Django interactive shell"
    echo "  just migrate          Apply migrations"
    echo "  just makemigrations   Create migrations"
    echo "  just dbshell          Database shell"
    echo "  just superuser        Create superuser"
    echo "  just urls             Show all URLs (django-extensions)"
    echo "  just collectstatic    Collect static files"
    echo ""
    echo "Testing & Quality:"
    echo "  just test             Run tests"
    echo "  just test-cov         Tests with coverage"
    echo "  just lint             Lint code"
    echo "  just format           Format code"
    echo "  just type-check       Type checking"
    echo "  just security         Security audit"
    echo "  just check            Quick CI check (lint + type + test)"
    echo "  just all-checks       Full quality gates"
    echo ""
    echo "Git Hooks:"
    echo "  just precommit        Run pre-commit on all files"
    echo ""
    echo "Cleanup:"
    echo "  just clean            Remove cache/build files"
    echo ""
    echo "Docker:"
    echo "  just docker-build     Build Docker image"
    echo "  just docker-run       Run with docker-compose"
    echo ""

# Configuration
TARGET := "apps"
PYTHON := "python"

# ============ SETUP ============
install:
    uv sync --group dev --group test

sync:
    uv sync

# ============ DEVELOPMENT ============
run:
    uv run {{PYTHON}} manage.py runserver 0.0.0.0:8000

shell:
    uv run {{PYTHON}} manage.py shell

migrate:
    uv run {{PYTHON}} manage.py migrate

makemigrations:
    uv run {{PYTHON}} manage.py makemigrations

superuser:
    uv run {{PYTHON}} manage.py createsuperuser

dbshell:
    uv run {{PYTHON}} manage.py dbshell

urls:
    uv run {{PYTHON}} manage.py show_urls

collectstatic:
    uv run {{PYTHON}} manage.py collectstatic --noinput

# ============ TESTING & QUALITY ============
test:
    uv run pytest

test-cov:
    uv run pytest --cov={{TARGET}} --cov-report=html --cov-report=term-missing
    @echo "✅ Coverage: htmlcov/index.html"

lint:
    uv run ruff check {{TARGET}}/

format:
    uv run ruff format {{TARGET}}/

type-check:
    uv run mypy {{TARGET}}/

security:
    uv run bandit -r {{TARGET}}/ -ll

precommit:
    uv run pre-commit run --all-files

# Quick local CI (like GitHub Actions)
check: lint type-check test
    @echo "✅ All quick checks passed!"

# Full quality gates (production ready)
all-checks: lint type-check security test
    @echo "✅ Full quality gates passed!"

# ============ CLEANUP ============
clean:
    rm -rf {{TARGET}}/__pycache__ **/__pycache__
    rm -rf .pytest_cache .mypy_cache htmlcov
    rm -rf .ruff_cache .bandit
    rm -f .coverage
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    @echo "✅ Cleaned!"

# Nuclear option: remove everything git ignores
clean-all:
    git clean -fdX
    @echo "✅ Deep clean complete!"

# ============ DEPLOYMENT ============
deploy: migrate collectstatic
    @echo "✅ Deployment prepared!"

# ============ DOCKER ============
docker-build:
    docker build -t django-app:latest .

docker-run:
    docker compose up --build

docker-stop:
    docker compose down
