# FastAPI Azure — Cosmic Missions API

A learning-focused FastAPI CRUD API backed by PostgreSQL (missions + nested crew members), with a pytest integration test suite, GitHub Actions CI/CD, and a live Azure deploy (App Service + Flexible Server). API routes are protected with an `X-API-KEY` header.

## Stack

- **FastAPI** + **Uvicorn**
- **SQLAlchemy** + **PostgreSQL** (`psycopg2`)
- **Pydantic** for request/response validation
- **API key auth** (`X-API-KEY` via `src/auth.py`)
- **pytest** with per-test transaction rollback
- **GitHub Actions** CI (`test.yml`) + Azure deploy (`main_rg-cosmic-missions.yml`)
- **Azure:** App Service (Python 3.13) + PostgreSQL Flexible Server

## Project structure

```
src/
  main.py          # FastAPI app, GET /health (open)
  routers.py       # /cosmic-missions routes (API key required)
  auth.py          # get_api_key dependency
  models.py        # SQLAlchemy models
  schemas.py       # Pydantic schemas
  database.py      # Engine, session, get_db

tests/
  conftest.py      # client_with_rollback, db_session, API key override
  test_*.py        # Tests by HTTP method + roundtrip

sql_files/
  create_cosmic_missions_table.sql
  create_crew_members_table.sql

docs/
  upgrade-roadmap.md
  api-testing-checklist.md

.github/
  workflows/
    test.yml                      # CI: Postgres service + pytest
    main_rg-cosmic-missions.yml   # CD: build + deploy to App Service
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

Edit `.env` with your local Postgres credentials and API key:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/cosmic_missions_db
TEST_DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/cosmic_missions_test_db
API_KEY=your-api-key-here
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

### 4. Create databases and tables

```bash
docker exec -it fastapi_postgres_db psql -U postgres -c "CREATE DATABASE cosmic_missions_db;"
docker exec -it fastapi_postgres_db psql -U postgres -c "CREATE DATABASE cosmic_missions_test_db;"

# Missions first, then crew (FK depends on parent table)
for db in cosmic_missions_db cosmic_missions_test_db; do
  docker exec -i fastapi_postgres_db psql -U postgres -d "$db" \
    < sql_files/create_cosmic_missions_table.sql
  docker exec -i fastapi_postgres_db psql -U postgres -d "$db" \
    < sql_files/create_crew_members_table.sql
done
```

Or copy the SQL files into the container and run them with `psql -f`.

## Run the API

```bash
cd src
uvicorn main:app --reload
```

- Health (no API key): http://localhost:8000/health
- API: http://localhost:8000/docs
- Mission/crew routes require header: `X-API-KEY: <your API_KEY>`

## API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Liveness check |
| `GET` | `/cosmic-missions` | API key | List all missions |
| `GET` | `/cosmic-missions/success` | API key | List successful missions only |
| `GET` | `/cosmic-missions/{id}` | API key | Get mission by ID |
| `GET` | `/cosmic-missions/{id}/telemetry` | API key | Get telemetry JSON |
| `POST` | `/cosmic-missions` | API key | Create mission |
| `PUT` | `/cosmic-missions/{id}` | API key | Full replace |
| `PATCH` | `/cosmic-missions/{id}` | API key | Partial update |
| `DELETE` | `/cosmic-missions/{id}` | API key | Delete mission (`ON DELETE CASCADE` removes crew) |
| `POST` | `/cosmic-missions/{id}/crew` | API key | Add crew member (`name`, `role`) |
| `GET` | `/cosmic-missions/{id}/crew` | API key | List crew for a mission |
| `DELETE` | `/cosmic-missions/{id}/crew/{crew_id}` | API key | Delete one crew member |

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

## CI / CD (GitHub Actions)

On every push to `main`:

- **Test** (`.github/workflows/test.yml`): Postgres 15 service → create tables → `uv run pytest`
- **Deploy** (`.github/workflows/main_rg-cosmic-missions.yml`): build → OIDC login → App Service

View results on GitHub → **Actions** tab, or locally:

```bash
gh run list
gh run view --log
```

## Learning docs

- [docs/upgrade-roadmap.md](docs/upgrade-roadmap.md) — evolution + Azure Phases 0–F (0–C + D1 done)
- [docs/api-testing-checklist.md](docs/api-testing-checklist.md) — pytest patterns and what to assert

## Roadmap

- [x] CRUD API with APIRouter
- [x] Isolated test database
- [x] Transaction rollback test fixtures
- [x] Test markers (`unit` / `integration`) — 15 unit, 35 integration (58 total)
- [x] Coverage reporting (~99% on `src/`)
- [x] GitHub Actions CI (`.github/workflows/test.yml`)
- [x] Foreign keys / nested crew members (`crew_members`)
- [x] Azure App Service + PostgreSQL Flexible Server (Phases 0–C)
- [x] API key auth (`X-API-KEY` / Phase D1)
- [x] GitHub Actions deploy to Azure (OIDC)
- [x] Managed Identity App Service → Postgres (Phase D2)
- [ ] Gate deploy on test success / CI polish (Phase E)
- [ ] Terraform IaC (Phase F)
