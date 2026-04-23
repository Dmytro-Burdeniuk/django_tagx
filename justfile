# Django Template - Universal Commands
# Usage: just help

@help:
    echo "🚀 Django Project - Available Commands"
    echo ""
    echo "Setup:"
    echo "  just install          Install all dependencies"
    echo ""
    echo "Docker:"
    echo "  just up               Run local stack (docker-compose.local.yml)"
    echo "  just down             Stop and clean local stack"
    echo ""
    echo "Development (Docker):"
    echo "  just shell            Django interactive shell"
    echo "  just migrate          Apply migrations"
    echo "  just makemigrations   Create migrations"
    echo "  just superuser        Create superuser"
    echo ""
    echo "Testing & Quality:"
    echo "  just test             Run tests"
    echo "  just test-cov         Tests with coverage"
    echo "  just lint             Lint code (local)"
    echo "  just format           Format code (local)"
    echo "  just type-check       Type checking (local)"
    echo "  just security         Security audit"
    echo "  just all-checks       All quality gates"
    echo ""
    echo "Git Hooks:"
    echo "  just precommit        Run pre-commit on all files"
    echo ""
    echo "Cleanup:"
    echo "  just clean            Remove cache/build files"
    echo ""

# Configuration
TARGET := "apps"
PYTHON := "python"

# ============ SETUP ============
install:
    uv sync --group dev --group test
    @echo "✅ All dependencies downloaded"

# ============ DOCKER ============
up:
    docker compose -f docker-compose.local.yml up

down:
    docker compose -f docker-compose.local.yml down -v --remove-orphans
    @echo "✅ Local stack stopped and cleaned"

# ============ DJANGO ============
migrate:
    docker compose -f docker-compose.local.yml exec django uv run python manage.py migrate

shell:
    docker compose -f docker-compose.local.yml exec django uv run python manage.py shell

makemigrations:
    docker compose -f docker-compose.local.yml exec django uv run python manage.py makemigrations

superuser:
    docker compose -f docker-compose.local.yml exec django uv run python manage.py createsuperuser

# ============ TESTING & QUALITY ============
test:
    docker compose -f docker-compose.local.yml exec django uv run pytest

test-cov:
    docker compose -f docker-compose.local.yml exec django uv run pytest --cov={{TARGET}} --cov-report=html --cov-report=term-missing
    @echo "✅ Coverage: htmlcov/index.html"

check:
    uv run pre-commit run --all-files

type:
    uv run mypy {{TARGET}}/

# ============ CLEANUP ============
clean:
    rm -rf {{TARGET}}/__pycache__ **/__pycache__
    rm -rf .pytest_cache .mypy_cache htmlcov
    rm -rf .ruff_cache .bandit
    #TODO: add cleanup for Claude generated files
    rm -f .coverage
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    @echo "✅ Cleaned!"
