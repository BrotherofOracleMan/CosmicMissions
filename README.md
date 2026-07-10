# FastAPI Azure — Cosmic Missions API

A learning-focused FastAPI CRUD API backed by PostgreSQL, with a pytest integration test suite, GitHub Actions CI, and a roadmap toward Azure deployment.

## Stack

- **FastAPI** + **Uvicorn**
- **SQLAlchemy** + **PostgreSQL** (`psycopg2`)
- **Pydantic** for request/response validation
- **pytest** with per-test transaction rollback
- **GitHub Actions** CI on push to `main`

## Project structure

```
src/
  main.py          # FastAPI app entry point
  routers.py       # /cosmic-missions routes
  models.py        # SQLAlchemy models
  schemas.py       # Pydantic schemas
  database.py      # Engine, session, get_db

tests/
  conftest.py      # client_with_rollback, db_session, fixtures
  test_*.py        # Tests by HTTP method + roundtrip

sql_files/
  create_cosmic_missions_table.sql

docs/
  upgrade-roadmap.md
  api-testing-checklist.md

.github/
  workflows/
    test.yml         # CI: Postgres service + pytest
```

## Prerequisites

- Python 3.13+
- PostgreSQL 16 (local Docker is fine)
- [uv](https://docs.astral.sh/uv/) or pip for dependencies

## Local setup

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd FASTAPI_azure
uv sync
# or: python -m venv .venv && source .venv/bin/activate && pip install -e .
```

Install dev dependencies for coverage:

```bash
uv sync --group dev
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your local Postgres credentials:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/cosmic_missions_db
TEST_DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/cosmic_missions_test_db
```

### 3. Start PostgreSQL

Example with Docker:

```bash
docker run -d \
  --name fastapi_postgres_db \
  -e POSTGRES_PASSWORD=YOUR_PASSWORD \
  -p 5432:5432 \
  postgres:16
```

### 4. Create databases and table

```bash
docker exec -it fastapi_postgres_db psql -U postgres -c "CREATE DATABASE cosmic_missions_db;"
docker exec -it fastapi_postgres_db psql -U postgres -c "CREATE DATABASE cosmic_missions_test_db;"

docker exec -it fastapi_postgres_db psql -U postgres -d cosmic_missions_db \
  -f /path/to/sql_files/create_cosmic_missions_table.sql

docker exec -it fastapi_postgres_db psql -U postgres -d cosmic_missions_test_db \
  -f /path/to/sql_files/create_cosmic_missions_table.sql
```

Or copy the SQL file into the container and run it with `psql -f`.

## Run the API

```bash
cd src
uvicorn main:app --reload
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/cosmic-missions` | List all missions |
| `GET` | `/cosmic-missions/success` | List successful missions only |
| `GET` | `/cosmic-missions/{id}` | Get mission by ID |
| `GET` | `/cosmic-missions/{id}/telemetry` | Get telemetry JSON |
| `POST` | `/cosmic-missions` | Create mission |
| `PUT` | `/cosmic-missions/{id}` | Full replace |
| `PATCH` | `/cosmic-missions/{id}` | Partial update |
| `DELETE` | `/cosmic-missions/{id}` | Delete mission |

### HTTP status codes

| Code | When |
|------|------|
| `200` | Success |
| `404` | Mission not found |
| `409` | Duplicate `mission_id` on POST |
| `422` | Invalid request body or path parameter |

## Tests

Tests use a **separate test database** (`TEST_DATABASE_URL`) and **transaction rollback** per test — no manual cleanup required.

```bash
pytest tests/ -v
```

Run subsets by marker:

```bash
pytest -m unit -v           # validation-only (422) tests
pytest -m integration -v    # DB-backed tests
```

Run with coverage:

```bash
uv sync --group dev
pytest --cov=src --cov-report=term-missing
```

## CI (GitHub Actions)

On every push to `main`, `.github/workflows/test.yml`:

1. Starts a Postgres 15 service container
2. Creates `cosmic_missions_test_db` and runs `sql_files/create_cosmic_missions_table.sql`
3. Installs dependencies with `uv sync`
4. Runs all 39 tests with `uv run pytest`

View results on GitHub → **Actions** tab, or locally:

```bash
gh run list
gh run view --log
```

## Learning docs

- [docs/upgrade-roadmap.md](docs/upgrade-roadmap.md) — project evolution: APIRouter, test DB, rollback, CI, foreign keys, Azure
- [docs/api-testing-checklist.md](docs/api-testing-checklist.md) — pytest patterns and what to assert

## Roadmap

- [x] CRUD API with APIRouter
- [x] Isolated test database
- [x] Transaction rollback test fixtures
- [x] Test markers (`unit` / `integration`) — 15 unit, 22 integration
- [x] Coverage reporting (100% on `src/`)
- [x] GitHub Actions CI (`.github/workflows/test.yml`)
- [ ] Foreign keys / related tables
- [ ] Deploy to Azure (App Service + PostgreSQL Flexible Server)
