# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**django_tagx** is a Django REST API backend for a street art & graffiti map mobile application. This is a university project (2–3 week MVP) that allows users to add graffiti locations, upload photos, vote on artwork existence, and browse nearby artworks with geolocation.

**Architecture:**
- Django + Django REST Framework
- PostgreSQL with PostGIS for geospatial queries
- JWT-based authentication
- Local or cloud-based media storage for images
- Mobile-ready REST API endpoints

---

## Core Features (MVP Scope)

1. **Authentication** — User registration, login via JWT, logout
2. **User System** — Basic profiles with ownership of posts
3. **Graffiti Map** — Create/read/update/delete graffiti locations with title, description, lat/lon coordinates
4. **Geolocation** — Search graffiti within a radius (1–5 km), sorted by distance
5. **Photo Upload** — Attach images to graffiti locations
6. **Voting System** — Users vote "exists" / "does not exist", one vote per user per item, prevent duplicates

---

## Project Structure (Expected)

```
django_tagx/
├── manage.py
├── requirements.txt
├── street_art/                 # Main Django project
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── api/                        # REST API app
│   ├── models.py              # User, Graffiti, Vote, Photo models
│   ├── serializers.py         # DRF serializers for validation
│   ├── views.py               # API views (CRUD, geolocation, voting)
│   ├── urls.py                # API route definitions
│   ├── permissions.py         # IsAuthenticated, IsOwner, etc.
│   ├── filters.py             # Geolocation filtering, pagination
│   └── tests/                 # Test suite (pytest, DRF test client)
├── media/                      # Uploaded images (local storage)
└── README.md
```

---

## Common Development Commands

### Setup & Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### Development Server
```bash
# Run Django development server (default: http://localhost:8000)
python manage.py runserver

# Run with custom host/port
python manage.py runserver 0.0.0.0:8080
```

### Database & Migrations
```bash
# Create new migration after model changes
python manage.py makemigrations

# Apply pending migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### Testing
```bash
# Run all tests
pytest

# Run tests for specific app
pytest api/tests/

# Run single test file
pytest api/tests/test_auth.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=api
```

### Linting & Code Quality
```bash
# Format code with Black
black .

# Check linting with flake8
flake8 api/

# Run isort for import sorting
isort .
```

### Admin & Utilities
```bash
# Django admin interface (creates superuser, manage data)
# Access at http://localhost:8000/admin

# Shell for quick database queries
python manage.py shell
```

---

## Key Development Considerations

### Authentication Flow
- JWT tokens issued on login (access + refresh tokens recommended)
- All protected endpoints require `Authorization: Bearer <token>` header
- Implement `IsAuthenticated` permission class on views that require login

### Geolocation & PostGIS
- Use `django-geospatial` or raw PostGIS queries with Django ORM
- Store coordinates as `PointField` in Graffiti model
- Filtering within radius uses `distance__lte` with `D()` distance objects
- Example: `Graffiti.objects.filter(coordinates__distance_lte=(user_point, D(km=5)))`

### Photo Upload
- Store images in Django's `media/` folder (development) or cloud storage (production optional)
- Use `ImageField` on Photo model with max file size validation
- Validate MIME type on upload endpoint

### Voting System
- Enforce one vote per user per graffiti with `unique_together` constraint
- Vote model: `(user, graffiti, vote_type)` with `vote_type` in ["exists", "does_not_exist"]
- Aggregate vote counts via annotated queries or cached counts

### Pagination
- Use DRF's `PageNumberPagination` or `CursorPagination` (cursor recommended for geolocation-sorted results)
- Default page size ~20 items, allow client to specify via `?page_size=` or `?limit=`

### Serializer Validation
- Validate coordinates (latitude -90 to 90, longitude -180 to 180)
- Validate image file size & format (JPEG, PNG)
- Ensure title/description are non-empty and reasonable length

---

## What NOT to Do (Scope Constraints)

- **Avoid complex DevOps**: No AWS EC2, Lambda, Kubernetes, or advanced Docker orchestration
- **Avoid microservices**: Keep it monolithic
- **Avoid real-time features**: No WebSockets, no live sync
- **Avoid enterprise patterns**: No Elasticsearch, no AI/ML, no message queues (unless absolutely necessary)
- **Avoid over-engineering**: Implement MVP only; skip optional features unless time permits

---

## Testing Strategy

- **Unit tests** — Test models (constraints, methods), serializers (validation)
- **Integration tests** — Test API endpoints (auth flow, CRUD, geolocation, voting)
- **Edge cases** — Duplicate votes, invalid coordinates, missing auth tokens, invalid images

Use DRF's `APITestCase` and `APIClient` for endpoint testing.

---

## API Endpoints (Planned)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Get JWT token |
| POST | `/api/auth/logout` | Invalidate token (optional) |
| GET | `/api/graffiti/` | List all graffiti (paginated) |
| GET | `/api/graffiti/?lat=X&lon=Y&radius=5` | Search by geolocation |
| POST | `/api/graffiti/` | Create graffiti (auth required) |
| GET | `/api/graffiti/{id}/` | Get single graffiti details |
| PATCH | `/api/graffiti/{id}/` | Update graffiti (owner only) |
| DELETE | `/api/graffiti/{id}/` | Delete graffiti (owner only) |
| POST | `/api/graffiti/{id}/photos/` | Upload photo (auth required) |
| POST | `/api/graffiti/{id}/votes/` | Vote on graffiti (auth required) |
| GET | `/api/graffiti/{id}/votes/` | Get vote counts |

---

## Dependencies (Expected in requirements.txt)

```
Django>=4.2
djangorestframework>=3.14
djangorestframework-simplejwt>=5.0
django-cors-headers>=4.0
django-filter>=23.0
Pillow>=9.0  # Image processing
psycopg2-binary>=2.9  # PostgreSQL driver
python-dotenv>=1.0
pytest>=7.0
pytest-django>=4.5
black>=23.0
flake8>=6.0
isort>=5.0
```

---

## Development Workflow

1. **Create feature branch** — `git checkout -b feature/your-feature`
2. **Write tests first** (or alongside implementation) — test new endpoints before deploying
3. **Implement feature** — models, serializers, views, URLs
4. **Run tests** — ensure all tests pass
5. **Format & lint** — `black . && flake8 && isort .`
6. **Commit with clear message** — reference feature/fix
7. **Create PR** — test on staging if available
8. **Merge to main** — deploy to production

---

## Useful Django & DRF Patterns

- **Custom Permissions** — Create `permissions.py` with `IsOwnerOrReadOnly` for ownership checks
- **Filtering & Ordering** — Use `django-filter` with `SearchFilter`, `OrderingFilter` for geolocation queries
- **Throttling** (Optional) — Basic rate limiting via DRF's `UserRateThrottle` if needed
- **Error Responses** — DRF provides structured error responses; use consistent HTTP status codes
- **API Documentation** — DRF's built-in schema generation; consider adding `/api/schema/` for Swagger/OpenAPI

