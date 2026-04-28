---
name: django-tests
description: Generate production-quality pytest/pytest-django test modules for Django code. Use whenever the user asks to write, improve, or review tests for Django code in this repository.
---

# Django Tests Skill

## Mission

Given Django source code, produce a complete, runnable pytest module that is concise, deterministic, and covers all significant behavior branches.

## Required output format

Always return exactly two sections:

1. **Analysis** (max 15 lines)
   - Unit(s) under test
   - Dependencies to mock
   - Numbered scenarios to cover

2. **Test module**
   - One fenced Python file per tested source file
   - Place under `tests/`
   - Complete, importable, and runnable with `pytest`

## Workflow

1. Identify public API of the unit under test.
2. Split dependencies into:
   - Must mock (external boundaries)
   - Can use directly (local/simple internals)
3. Enumerate scenarios:
   - Happy path
   - Edge cases
   - Invalid input
   - Permission/validation failures
   - Exception/error paths
4. Implement tests with clear Arrange / Act / Assert structure.

## Core rules

- Use `pytest` + `pytest-django`.
- Avoid `unittest.TestCase` unless explicitly requested.
- One unit per test function; one logical assertion group.
- Test names: `test_<expected_behavior>`.
- Use `pytest.raises` for exceptions.
- Use `pytest.mark.parametrize` only when readability improves.
- Prefer fixtures/model-bakery over heavy inline setup.
- Keep tests deterministic (pin time/UUID/random where relevant).
- Assert observable behavior and key side effects, not implementation internals.
- Do not invent behavior not present in source.

## Mocking policy

Always mock:
- Third-party HTTP/API calls
- Celery task dispatch
- Email/SMS sending
- File/object-storage I/O
- Environment/settings overrides
- Clock/UUID/random when behavior depends on them

Mock only when needed:
- ORM reads (prefer real DB for simple lookups)
- Django cache (LocMemCache default unless hit/miss branching is tested)
- Logging (only when log assertions are part of behavior)

Use `pytest-mock` (`mocker`) for patching.
If ORM is tightly coupled, use `@pytest.mark.django_db` with minimal setup and a short reason comment.

## Django-specific test focus

- Models: custom methods/business rules only.
- Managers/QuerySets: filtering logic and annotations
- Serializers: validation, transforms, create/update, error cases.
- Views/ViewSets: isolate request handling/permissions/response shape; mock service layer; HTTP behavior (status codes, permissions, response shape).
- Forms: validation and `cleaned_data` behavior.
- Services: core business logic (primary unit of testing)
- Selectors: read/query logic, optimized DB access
- Signals: test only when behavior relies on signal wiring.
- Permissions: explicit allowed and denied tests.
- Management commands: mock I/O/external calls; verify command outcomes.

## DRF ViewSet testing — pitfalls

**Use `APIClient` + router URLs, never `ViewSet.as_view()` directly.**
`@action(permission_classes=[...])` kwargs are only applied when the router calls `as_view()` with
them as `initkwargs`. Calling `ViewSet.as_view({"post": "action"})` directly ignores all
`@action`-level `permission_classes`, `authentication_classes`, and `serializer_class` — only
class-level defaults apply. Always go through the actual registered URL.

**Before hardcoding URLs, verify what the router generated.**
`@action(url_path="")` is falsy, so DRF uses the method name instead of an empty string.
Inspect the URL patterns to confirm: `[print(sp.pattern, sp.name) for sp in router.urls]`

**Anonymous users failing a permission check get 401, not 403.**
`APIView.permission_denied()` raises `NotAuthenticated` (401) when the user has no successful
authenticator, regardless of which permission class rejected the request.

**`get_queryset()` user-scoping causes 404 for non-owners, not 403.**
`get_object()` raises `Http404` before any ownership check code in the view body runs.

**`HasAPIKey`: create a real key, don't patch the permission class.**
Use `APIKey.objects.create_key(name="test")` and set `Authorization: Api-Key {key}` on the
client. Patching `has_permission` is unreliable through full URL routing.

**Session-backed permission tests: set the session and call `.save()` before the request.**
`client.session["key"] = val; client.session.save()` — the cookie is sent automatically.

## Environment assumptions

- Python 3.12
- Django 4.2+
- `pytest`, `pytest-django`, `pytest-mock`

## Quality bar

Suites must be production-grade:
- meaningful branch coverage
- compact and non-redundant assertions
- stable/non-flaky execution
- ready for professional code review
