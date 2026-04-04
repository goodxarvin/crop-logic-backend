# Repository Guidelines

## Project Structure & Module Organization
This repository is a Django REST backend organized by app domains. Core configuration lives in `config/` (`settings.py`, `urls.py`, `celery.py`). Feature apps (for example `account/`, `farm_hub/`, `sensor_catalog/`, `crop_zoning/`, `notifications/`) each contain `models.py`, `serializers.py`, `views.py`, `urls.py`, and app-specific `migrations/`.

Tests are mostly colocated in each app as `tests.py`. Mock payloads and integration fixtures are stored under `json/mock_data/` and `external_api_adapter/json/`. API collections are under `*/postman/`.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` - create and activate a virtual environment.
- `pip install -r requirements.txt` - install runtime and development dependencies.
- `python manage.py migrate` - apply database migrations.
- `python manage.py runserver` - start the local API server.
- `python manage.py test` - run the full Django test suite.
- `python manage.py test farm_hub` - run tests for a single app.
- `docker compose up --build` - run the backend and dependencies via Docker.

## Coding Style & Naming Conventions
Follow standard Django/Python conventions:
- 4-space indentation, snake_case for functions/variables, PascalCase for classes.
- Keep serializers in `serializers.py`, business logic in `services.py`, and routing in `urls.py`.
- Name management commands as verbs (for example `seed_admin_user`).
- Prefer small, app-scoped modules over cross-app imports unless shared behavior is intentional.

## Testing Guidelines
Use Django’s built-in test runner (`unittest` style). Place tests in each app’s `tests.py` (or `tests/` package if expanded). Name tests as `test_<behavior>` and cover serializers, view responses, and service edge cases. Use `unittest.mock.patch` for external integrations (AI adapters, SMS, or HTTP services).

## Commit & Pull Request Guidelines
Current history uses generic messages (`UPDATE`), but contributors should use clear, imperative commits such as `add sensor catalog seed command`.

For PRs, include:
- concise description of scope and affected apps,
- migration notes (`manage.py makemigrations`/`migrate` impact),
- test evidence (`python manage.py test ...` output),
- linked issue/task ID when available,
- request/response examples for API changes (Postman or JSON sample paths).

## Security & Configuration Tips
Copy `.env.example` to `.env` and never commit secrets. Validate CORS/JWT settings in `config/settings.py` per environment. Keep mock JSON and seed data free of production credentials or personal data.
