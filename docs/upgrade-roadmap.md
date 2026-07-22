# Upgrade Roadmap: APIRouter + Test Suite

A learning-focused guide and next steps for this project. Companion to [api-testing-checklist.md](api-testing-checklist.md).

You have a solid baseline: cosmic missions CRUD API with nested **crew members** (FK + `ON DELETE CASCADE`), pytest coverage across HTTP methods, an `APIRouter` refactor, an isolated test database, per-test transaction rollback, test markers, coverage reporting, and GitHub Actions CI. **Azure Phases 0–C and D1 are done**: Flexible Server + App Service + GitHub OIDC deploy + `X-API-KEY` on mission/crew routes. Optional next skill: **stubs/mocks**. Remaining Azure work: **Managed Identity for Postgres (D2)**, tighter CI/CD gating (E), and **Terraform (F)**. This doc explains what changed, why it helps, and what to tackle next.

---

## Part 1: API structure with `APIRouter`

### Current structure (done)

Routes are split between a thin app entry point and a dedicated router module:

```
src/
  main.py       # FastAPI app, include_router, GET /health (open)
  routers.py    # /cosmic-missions routes (API key required)
  auth.py       # get_api_key via X-API-KEY header
  database.py
  models.py
  schemas.py
```

**`main.py`** wires the app:

```python
app = FastAPI()
app.include_router(cosmic_missions_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

**`routers.py`** owns the feature:

- `router = APIRouter(prefix="/cosmic-missions", tags=["cosmic-missions"])`
- Mission CRUD: GET, POST, PUT, PATCH, DELETE
- Nested crew routes: `POST/GET /{mission_id}/crew`, `DELETE /{mission_id}/crew/{crew_member_id}`
- Same `Depends(get_db)` pattern throughout

Route decorators use paths relative to the prefix: `@router.get("")`, `@router.get("/success")`, `@router.get("/{mission_id}")`, `@router.post("/{mission_id}/crew")`, etc.

```mermaid
flowchart LR
    tests[TestClient] --> main[main.py]
    main --> router[routers.py]
    router --> db[(PostgreSQL via .env)]
```

### Why this is better than one big `main.py`

| Area | Single-file app | With `APIRouter` |
|------|-----------------|------------------|
| Organization | One file, all concerns | Feature file per domain |
| Scaling | Gets crowded fast | Add more routers later without touching missions |
| OpenAPI docs | One flat list | Grouped by `tags=` in Swagger UI |
| Testing | Import whole `app` | Same full-app tests; can optionally test router in isolation |
| Team workflow | Merge conflicts on one file | Parallel work on separate routers |
| Reusability | N/A | Mount same router under different prefixes if needed |

### What did not change

- URL paths (`/cosmic-missions`, `/cosmic-missions/success`, etc.)
- Pydantic schemas, SQLAlchemy models, `get_db`
- Existing tests — they should pass with zero assertion changes after a structure-only move

### Optional next API upgrades

- `status_code=201` on POST
- Move to `routers/cosmic_missions.py` if you add more router files
- Service layer (`services/cosmic_missions.py`) to keep routers thin
- Custom exception handlers for consistent error JSON

---

## Part 2: Upgrade the pytest test suite

### Current test-suite structure (done)

- **58 tests** across 7 files by HTTP concern: post, get, put, patch, delete, roundtrip, database (includes crew nested routes)
- Tests use **real PostgreSQL**, but now through a dedicated test database: `cosmic_missions_test_db`
- `tests/conftest.py` owns shared pytest setup: `db_session`, `client_with_rollback`, dependency override, per-test transaction rollback, and reusable data fixtures (missions + crew)
- `tests/payloads/missions.py` owns reusable mission/crew payloads and shared test IDs
- `tests/assertions.py` owns small `verify_*` helper functions for repeated assertions

Current layout:

```
tests/
  conftest.py                 # fixtures + FastAPI test DB override
  assertions.py               # verify_* helpers
  payloads/
    __init__.py
    missions.py               # shared mission payloads and IDs
  test_cosmic_missions_get.py
  test_cosmic_missions_post.py
  test_cosmic_missions_put.py
  test_cosmic_missions_patch.py
  test_cosmic_missions_delete.py
  test_cosmic_missions_roundtrip.py
  test_database.py
```

`.github/workflows/test.yml` is a reusable workflow (`workflow_call`) that runs the full suite via a Postgres service container. The deploy workflow calls it on every push to `main` before shipping.

### Problems this solved

| Issue | Example in your tests |
|-------|----------------------|
| Dev data risk | Tests no longer mutate `cosmic_missions_db` |
| Hidden seed dependency | GET tests now create Apollo 11 through a fixture |
| Repeated setup | One shared `client_with_rollback` fixture replaces per-file `TestClient(app)` setup |
| Duplicated payloads | Shared payloads live in `tests/payloads/missions.py` |
| Duplicated assertions | Repeated checks live in `tests/assertions.py` |
| Fixture duplication | PUT/PATCH/DELETE setup uses shared fixtures from `conftest.py` |
| Manual DELETE teardown | Per-test transaction rollback replaces `client.delete(...)` after fixtures |
| CI automation | GitHub Actions runs `pytest` (reusable `test.yml`) before deploy with ephemeral Postgres |

### Test database isolation (done)

Tests use a separate Postgres database and override `get_db` so production/dev data is never touched.

```mermaid
flowchart TD
    test[TestClient] --> app[FastAPI app]
    app --> override["Depends override: get_db → db_session"]
    override --> txn[Outer transaction per test]
    txn --> testDb[(Test DB)]
    test --> rollback[Rollback after test]
    rollback --> testDb
```

What is in place:

- `.env` has `DATABASE_URL` for dev and `TEST_DATABASE_URL` for tests
- `cosmic_missions_test_db` exists in the Postgres container (`fastapi_postgres_db`)
- `cosmic_missions` and `crew_members` tables exist in the test database
- `conftest.py` creates a test SQLAlchemy engine/session from `TEST_DATABASE_URL`
- `db_session` fixture opens an outer transaction per test and rolls it back in teardown
- `SessionLocal` uses `join_transaction_mode="create_savepoint"` so route-level `db.commit()` calls do not permanently persist test data
- `client_with_rollback` fixture overrides `get_db` to yield the shared `db_session`
- Tests create their own data through fixtures; teardown is automatic via rollback

What stayed the same:

- Endpoint paths
- Response status codes
- Pydantic schemas
- SQLAlchemy models
- Overall behavior being tested

### Fixtures now in `conftest.py`

| Fixture | Purpose |
|---------|---------|
| `db_session` | One SQLAlchemy session per test inside an outer transaction; rolled back after each test |
| `client_with_rollback` | Shared `TestClient` wired to `db_session` via `get_db` override |
| `apollo_11_mission` | Creates Apollo 11 via POST for GET tests |
| `test_mission` | Creates a mission for duplicate-ID POST testing |
| `successful_and_unsuccessful_missions` | Creates one successful and one unsuccessful mission |
| `mission_with_null_telemetry` | Creates a mission with `telemetry_data = None` |
| `created_mission` | Shared create fixture for PUT and PATCH tests |
| `created_minimal_mission` | Shared create fixture for DELETE tests |
| `crew_member_1` / `crew_member_2` | POST crew under `apollo_11_mission`; yield API response JSON |
| `mission_with_crew` | Packages Apollo + both crew members for list tests |
| `mission_with_crew_size_zero` | Mission with `crew_size=0` and no crew rows (empty list tests) |

### Payloads and assertion helpers

`tests/payloads/missions.py` now holds reusable data like:

- `APOLLO_11`
- `BASE_MISSION`
- `FULL_PUT_UPDATE`
- `DUPLICATE_TEST_MISSION`
- `SUCCESSFUL_MISSION`
- `UNSUCCESSFUL_MISSION`
- `NULL_TELEMETRY_MISSION`
- `MINIMAL_MISSION`
- `MISSION_WITH_CREW_SIZE_ZERO`
- `CREW_MEMBER_1`, `CREW_MEMBER_2` (create bodies: `name` + `role` only)
- `ROUNDTRIP_CREATE`, `ROUNDTRIP_PATCH`, `ROUNDTRIP_PUT`

`tests/assertions.py` now holds:

- `verify_mission_fields()`
- `verify_path_int_parsing_error()`

### Other pytest upgrades (optional next steps)

Markers, coverage, and CI are done. Remaining ideas:

1. **Stubs and mocks** — see the section below (ordered by importance for this project)
2. **`pytest.mark.parametrize` expansion** — same pattern for PATCH/PUT invalid bodies
3. **`pytest.raises` / error helpers** — useful if you add service-layer unit tests
4. **Factory helpers** — `make_mission_payload(**overrides)` if static payloads feel rigid
5. **HTTP status polish** — assert `201` on POST if you change the API
6. **CI enhancements** — add `pull_request` trigger, `--cov=src` in the workflow, or split unit/integration jobs

### Stubs and mocks (order of importance)

Your suite already uses **real Postgres** + transaction rollback for integration tests. Stubs and mocks are the next testing skill when you want **faster unit tests**, **failure injection**, or to isolate **external services** (Azure, email, HTTP APIs) without calling the real thing.

**Quick definitions**

| Term | What it is | Example in this project |
|------|------------|-------------------------|
| **Stub** | Stand-in that returns canned data; you do not inspect how it was used | Fake `get_db` that yields a fixed session |
| **Mock** | Stand-in that you also assert on (was it called? with what args?) | `MagicMock` session where you assert `query(...).filter(...).first()` was called |
| **Dependency override** | FastAPI’s way to swap a `Depends(...)` for tests | `app.dependency_overrides[get_db] = ...` (you already do this) |

```mermaid
flowchart TD
    integrate[Prefer real DB + rollback for CRUD] --> override[1. Dependency overrides]
    override --> session[2. Stub/mock the DB Session]
    session --> unittest[3. unittest.mock / pytest-mock]
    unittest --> external[4. Stub external APIs when you add them]
    external --> service[5. Service-layer unit tests]
```

Learn these in this order — each builds on the one above.

#### 1. Dependency overrides (most important — already done)

This is FastAPI’s primary testing seam. You already swap `get_db` for a test session:

```python
app.dependency_overrides[get_db] = override_get_db
```

**Why it ranks first:** almost every FastAPI tutorial and production app starts here. You keep the full HTTP stack (`TestClient` → router → Pydantic) while controlling what the handler depends on. Re-read Step 6 if this still feels fuzzy — stubs/mocks below are optional refinements of the same idea.

When you add more dependencies later (`get_current_user`, `get_blob_client`, …), override those the same way instead of reaching for `patch` first.

#### 2. Stub or mock the SQLAlchemy `Session` (true unit tests, no Postgres)

Integration tests with `client_with_rollback` should stay the default for CRUD. Use a fake session when you want:

- Tests that run without Docker / CI Postgres
- Failure paths that are painful to force in a real DB (`db.commit()` raises, connection drops)
- Pure unit tests of a future service function that takes `db: Session`

Minimal stub (return canned rows, ignore call history):

```python
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from routers import get_cosmic_mission_by_id

def test_get_mission_not_found_unit():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_cosmic_mission_by_id(999999, db)

    assert exc_info.value.status_code == 404
```

Or wire the stub through FastAPI (still no Postgres):

```python
def test_get_404_with_stub_session():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        response = client.get("/cosmic-missions/999999")
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"
```

**Keep both layers:** mark stubbed tests `@pytest.mark.unit` and DB tests `@pytest.mark.integration`. Do not replace your integration tests — stubs catch logic; Postgres catches SQL, constraints, and savepoint behavior.

#### 3. `unittest.mock.patch` / `pytest-mock` (isolate one call site)

Use when the code under test calls something you cannot inject via `Depends`:

```python
from unittest.mock import patch

@patch("routers.some_helper")
def test_helper_failure_returns_500(mock_helper, client_with_rollback):
    mock_helper.side_effect = RuntimeError("boom")
    # …call endpoint that uses some_helper…
```

Or with `pytest-mock` (`mocker` fixture):

```python
def test_helper_failure(mocker, client_with_rollback):
    mocker.patch("routers.some_helper", side_effect=RuntimeError("boom"))
    # …
```

**Why it ranks third:** powerful, but easy to overuse. Prefer dependency overrides when you control the signature. Reach for `patch` when the seam is a module-level import (helpers, SDK clients constructed inside a function).

#### 4. Stub external services (grows important as you approach Azure)

Once Step 9 (or stretch goals) adds outbound I/O — Blob Storage, SendGrid, `httpx` to another API — those must not hit the network in unit tests.

| Pattern | When |
|---------|------|
| Wrap the client in a FastAPI dependency, then override it | Best default for Azure SDKs |
| `respx` / `httpx` mock transport | Outbound HTTP with `httpx` |
| `MagicMock` with fixed return values | Simple SDK method (`upload_blob`, `send`) |

Sketch for a future dependency:

```python
# production
def get_storage():
    return BlobServiceClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))

# test
fake_storage = MagicMock()
fake_storage.get_blob_client.return_value.download_blob.return_value.readall.return_value = b"{}"
app.dependency_overrides[get_storage] = lambda: fake_storage
```

Until you have external I/O, skip this tier — there is nothing to stub yet.

#### 5. Service-layer stubs (only after you extract a service)

If you pull logic into `services/cosmic_missions.py`, unit-test the service with a stubbed session, and keep router tests thinner (HTTP + status codes). Until that refactor exists, prefer levels 1–2.

### What to keep from your current suite

- File-per-HTTP-method layout — still readable
- Explicit assertions (no over-abstracted helpers) — good for learning
- Roundtrip file — becomes even more valuable with isolated DB
- Parametrize for validation errors — keep expanding, not replacing
- Prefer real DB + override over heavy mocking for CRUD — stubs complement, not replace, Step 6

---

## Recommended learning order

```mermaid
flowchart TD
    baseline[Original: tests on dev DB] --> router[Refactor: APIRouter]
    router --> testDb[Add test DB + get_db override]
    testDb --> conftest[Shared conftest fixtures]
    conftest --> payloads[Move payloads + verify helpers]
    payloads --> rollback[Per-test transaction rollback]
    rollback --> ci[CI with test Postgres]
    ci --> fkeys[Foreign keys + crew members]
    fkeys --> stubs[Stubs and mocks optional]
    stubs --> azure[Deploy to Azure]
    azure --> auth[API auth + Managed Identity]
    auth --> tf[Terraform IaC]
```

| Step | Task | Effort | Status |
|------|------|--------|--------|
| 1 | APIRouter refactor | S | Done |
| 2 | Test DB + dependency override | M | Done |
| 3 | Shared `conftest.py` fixtures | S | Done |
| 4 | Decouple GET tests from seed CSV/dev data | M | Done |
| 5 | Payload folder + assertion helpers | S | Done |
| 6 | Transaction rollback cleanup | M | Done |
| 7 | Markers, coverage, CI | L | Done |
| 8 | Foreign keys and related tables (`crew_members`) | M–L | Done |
| 7b | Stubs and mocks (optional skill) | S–M | Optional / anytime |
| 9 | Deploy to Azure (portal → auth → CI/CD → Terraform) | L | In progress — 0–E done; F next |

---

## Step 6: Transaction rollback cleanup (Done)

Each test runs inside a database transaction that is **rolled back** when the test finishes. Fixtures create data through the API; teardown is automatic — no `DELETE` after `yield`.

### How it works

```text
Test starts  → db_session opens outer transaction
Fixture/test → POST/PUT/PATCH/DELETE via client_with_rollback
Route commit → releases savepoint only (not outer transaction)
Test ends    → transaction.rollback() in db_session teardown
DB state     → back to pre-test state
```

```mermaid
flowchart TD
    start[Test starts] --> txn[db_session: open outer transaction]
    txn --> client[client_with_rollback overrides get_db]
    client --> api[TestClient calls API]
    api --> db[Rows inserted/updated/deleted in test DB]
    db --> assert[Assertions]
    assert --> rollback[db_session teardown: rollback]
    rollback --> clean[DB back to pre-test state]
```

### `conftest.py` setup

```python
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    join_transaction_mode="create_savepoint",
)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client_with_rollback(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### Why savepoints matter

Your route handlers call `db.commit()` after writes. Without `join_transaction_mode="create_savepoint"`, those commits would permanently persist test data and rollback would not undo fixture setup.

### What changed from DELETE teardown

| Before (`DELETE` after test) | After (transaction rollback) |
|------------------------------|------------------------------|
| `client.delete(...)` in fixture teardown | No manual cleanup in fixtures |
| Failed tests could leave orphaned rows | Rollback runs even if test fails |
| Extra HTTP round-trips for cleanup | Faster teardown |
| Leftover rows caused `409` conflicts | Each test starts from a clean transaction |

Example fixture — setup only, no DELETE:

```python
@pytest.fixture
def apollo_11_mission(client_with_rollback: TestClient) -> Generator[dict, None, None]:
    response = client_with_rollback.post("/cosmic-missions", json=APOLLO_11)
    assert response.status_code == 200
    yield APOLLO_11
```

All tests use `client_with_rollback`. The old `client` fixture and `get_test_db` helper were removed.

### Clearing a dirty test DB (one-time recovery)

If you ran tests before rollback was fully wired, leftover rows may still exist in `cosmic_missions_test_db`. Truncate via Docker:

```bash
docker exec -it fastapi_postgres_db psql -U postgres -d cosmic_missions_test_db -c \
  "TRUNCATE TABLE cosmic_missions;"
```

After rollback is in place, you should not need this routinely.

---

## Step 7: Markers, coverage, CI (Done)

Step 7 made the suite faster to run in subsets, measurable with coverage, and automatic in CI (now called from the deploy workflow before ship).

### Part A: Test markers (done)

All tests are tagged `@pytest.mark.integration` or `@pytest.mark.unit` in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "integration: tests that require database access",
    "unit: tests that validate request/response without DB side effects",
]
```

| Marker | Count | Examples |
|--------|-------|----------|
| `integration` | 35 | CRUD, crew nested routes, 404 lookups, 409 duplicate, roundtrip |
| `unit` | 15 | invalid path param (`/abc`), parametrized POST/crew 422s |

Run subsets locally:

```bash
pytest -m unit -v
pytest -m integration -v
```

### Part B: Coverage with `pytest-cov` (done)

`pytest-cov` is in the dev dependency group. Run locally:

```bash
uv sync --group dev
pytest --cov=src --cov-report=term-missing
```

Current baseline: **~99% line coverage** on `src/` (58 tests). The small gap is the rare crew `IntegrityError` branch in `routers.py`. `database.py` is covered via `tests/test_database.py`, which exercises the real `get_db()` generator.

Coverage is a guide, not a goal by itself — use it to spot untested branches after refactors.

### Part C: CI pipeline — GitHub Actions (done)

Reusable workflow: `.github/workflows/test.yml` (`on: workflow_call`)  
Caller: `.github/workflows/main_rg-cosmic-missions.yml` (`test: uses: …` then `deploy: needs: [build, test]`)

```mermaid
flowchart LR
    push[Push to main] --> caller[Deploy workflow]
    caller --> testJob[Reusable test.yml]
    testJob --> pg[(Postgres 15 service container)]
    testJob --> setup[uv sync + psql create DB/table]
    setup --> pytest[uv run pytest]
    caller --> build[build]
    pytest --> gate{tests pass?}
    build --> gate
    gate -->|yes| deploy[deploy to App Service]
    gate -->|no| stop[Deploy skipped]
```

What the reusable test workflow does:

1. Starts a `postgres:15` service container with health checks
2. Sets `DATABASE_URL` and `TEST_DATABASE_URL` to the CI test database only (never Azure prod)
3. Checks out code, installs `uv`, runs `uv sync`
4. Installs `postgresql-client`, creates `cosmic_missions_test_db`, runs `create_cosmic_missions_table.sql` then `create_crew_members_table.sql`
5. Runs `uv run pytest` (all 58 tests)

View results: GitHub repo → **Actions** tab, or locally with `gh run list` / `gh run view --log`.

```text
Local (your Mac)          CI (GitHub runner)
─────────────────         ──────────────────
Docker Postgres           Postgres service container
.env credentials          test.yml env: block
You run pytest            Called via workflow_call before deploy
```

### Optional CI enhancements (not implemented)

- Add `pull_request:` trigger so PRs run tests before merge
- Add `pytest --cov=src` to the workflow
- Split into separate unit and integration jobs

---

## Step 8: Foreign keys and related tables (Done)

Step 8 added a **child table** `crew_members` linked to `cosmic_missions` by foreign key — one-to-many (one mission, many crew; each crew row has one `mission_id`).

```mermaid
erDiagram
    cosmic_missions ||--o{ crew_members : has
    cosmic_missions {
        int mission_id PK
        string mission_name
        string destination
    }
    crew_members {
        int crew_member_id PK
        int mission_id FK
        string name
        string role
    }
```

### What shipped

| Piece | Location |
|-------|----------|
| SQL | `sql_files/create_crew_members_table.sql` — `SERIAL` PK, `REFERENCES cosmic_missions(mission_id) ON DELETE CASCADE` |
| Models | `CrewMember` + `relationship(..., cascade="all, delete-orphan")` on `CosmicMission` |
| Schemas | `CrewMemberBase` (response), `CrewMemberCreate` (`name`/`role` only, `min_length=1`) |
| Routes | Nested under `/cosmic-missions/{mission_id}/crew` |
| Fixtures | Parent first (`apollo_11_mission`), then `crew_member_*`, `mission_with_crew` |
| CI | Workflow runs both create-table SQL files on the test DB |

### Nested routes

| Route | Purpose |
|-------|---------|
| `POST /cosmic-missions/{mission_id}/crew` | Add crew (`name`, `role` in body; path supplies `mission_id`) |
| `GET /cosmic-missions/{mission_id}/crew` | List crew for a mission (`[]` if none) |
| `DELETE /cosmic-missions/{mission_id}/crew/{crew_member_id}` | Remove one crew member (both ids must match) |

### Delete behavior

- **DB:** `ON DELETE CASCADE` — deleting a mission removes its crew rows in Postgres
- **ORM:** `cascade="all, delete-orphan"` on `crew_members` so SQLAlchemy does not try to NULL `mission_id` on parent delete (which would violate `NOT NULL`)

### Tests covered (examples)

1. Happy path — POST/GET crew; empty list when no crew
2. Missing parent mission → `404`
3. Invalid body / path → `422` (including empty strings via `min_length`)
4. DELETE crew happy path; missing crew; wrong mission/crew pair → `404`
5. Cascade — DELETE mission with crew → follow-up GET `.../crew` → `404` mission not found

### Optional stretch goals

- Eager-load crew with missions: `db.query(CosmicMission).options(joinedload(CosmicMission.crew_members))`
- Alembic migrations instead of raw SQL files
- Replace `telemetry_data` JSONB with a `telemetry_events` child table (queryable history)
- Many-to-many if the same person must belong to multiple missions (join table)

---

## Step 9: Deploy to Azure (In progress)

Move from **local Docker Postgres + uvicorn on your machine** to a hosted FastAPI API and managed PostgreSQL in Azure. Learn in this order: **Portal first** → **protect prod access** (API key, then Managed Identity for Postgres) → **CI/CD deploy** → **Terraform**.

Your app already reads `DATABASE_URL` (and `API_KEY`) from the environment — that pattern maps directly to Azure App Settings / Environment variables.

### Current status (what you have live)

| Phase | Status | Notes |
|-------|--------|--------|
| 0 — Repo prep | **Done** | `requirements.txt`, `GET /health`, `.gitignore` |
| A — Flexible Server | **Done** | `rg-cosmic-missions`, server `rg-cosmic-missions-database`, DB `cosmic_missions_db`, both SQL files applied |
| B — App Service | **Done** | Web App `rg-cosmic-missions`, Python 3.13, Free plan; `DATABASE_URL`, `PYTHONPATH=src`, startup `uvicorn` |
| C — Verify | **Done** | `/health`, CRUD, crew smoke-tested on Azure |
| D1 — API key | **Done** | `src/auth.py` + router `dependencies`; `API_KEY` in `.env` / Azure; pytest overrides `get_api_key` |
| D2 — Managed Identity → Postgres | **Done** | System MI + Postgres role; `database.py` uses token when `DATABASE_URL` unset |
| E — CI/CD polish | **Done** | Deploy `needs: [build, test]`; reusable `test.yml`; `TEST_DATABASE_URL` in test job only |
| F — Terraform | **Not started** | |

**Live hostname (example):** `https://rg-cosmic-missions-cghta5dsfxb5fven.canadacentral-01.azurewebsites.net`  
**Deploy workflow:** `.github/workflows/main_rg-cosmic-missions.yml` (OIDC + user-assigned identity `oidc-msi-ad6c`; calls test before deploy)  
**Test workflow:** `.github/workflows/test.yml` (`workflow_call` — CI Postgres / `TEST_DATABASE_URL` only)

### Target architecture

```mermaid
flowchart LR
    client[API clients] -->|"X-API-KEY"| app[Azure App Service Linux]
    app -->|password URL today MI later| pg[(PostgreSQL Flexible Server)]
    gh[GitHub Actions] -->|OIDC deploy| app
    gh -->|pytest in CI| testPg[(Postgres service container)]
    tf[Terraform] -->|later| rg[Resource group]
    rg --> app
    rg --> pg
```

| Local | Azure (now) |
|-------|-------------|
| Docker `postgres` on `localhost:5432` | Flexible Server `rg-cosmic-missions-database` |
| `uvicorn` manually | App Service Linux, Python 3.13 |
| `.env` | App Service **Environment variables** |
| API key in `.env` | Same `API_KEY` setting in Azure |
| Password in `DATABASE_URL` | Password + `sslmode=require` (D2 removes password) |
| pytest / `TEST_DATABASE_URL` | CI Postgres only — never Azure prod |

**Why Flexible Server:** PostgreSQL + `psycopg2` + JSONB — closest lift.  
**Why App Service:** simplest FastAPI + `uvicorn` host.  
**IAM today:** OIDC managed identity for **deploy only**. Runtime DB still uses password; callers use **API key** (app auth, not Entra).

### Azure resources (created)

1. Resource group `rg-cosmic-missions`
2. PostgreSQL Flexible Server `rg-cosmic-missions-database` (Burstable B1ms)
3. Database `cosmic_missions_db` + both create-table SQL files
4. App Service plan (Linux, Free) + Web App `rg-cosmic-missions`
5. GitHub Actions deploy via Deployment Center (user-assigned identity + Contributor RBAC)
6. App settings: `DATABASE_URL`, `PYTHONPATH=src`, `API_KEY`, startup command

---

### Phase 0 — Repo prep (Done)

| Task | Status |
|------|--------|
| `requirements.txt` via `uv export --no-dev` | Done |
| `PYTHONPATH=src` + startup `uvicorn main:app --host 0.0.0.0 --port 8000` | Done (Azure) |
| `GET /health` → `{"status":"ok"}` | Done (`main.py`, no API key) |
| `.gitignore` excludes `.env` | Done |

---

### Phase A — Database (Done)

Completed in Portal: resource group, Flexible Server (B1ms), `cosmic_missions_db`, firewall (client IP + Azure services), both SQL files via `psql`, Mac → Azure smoke test with `sslmode=require`.

Connection string shape (still password-based until D2):

```text
postgresql://<admin>:<password>@rg-cosmic-missions-database.postgres.database.azure.com:5432/cosmic_missions_db?sslmode=require
```

Keep Azure prod DB out of pytest.

---

### Phase B — App Service (Done)

Linux Web App, Python 3.13, Environment variables (`DATABASE_URL`, `PYTHONPATH`), startup command, GitHub Actions deploy (`main_rg-cosmic-missions.yml`).

Deploy IAM: user-assigned identity + federated credential for `repo:…/CosmicMissions:ref:refs/heads/main` + **Contributor** (Website Contributor alone caused “No subscriptions found”).

---

### Phase C — Verify (Done)

Confirmed against the live App Service URL:

1. `GET /health` → `{"status":"ok"}` (no API key)
2. `/docs` loads
3. Mission CRUD + crew nested routes against Azure Postgres

**Debug order:** Log stream → missing App Setting → firewall / `sslmode` → tables not created → missing `API_KEY` (401 on all mission routes).

---

### Phase D — Authentication when hitting prod data

Two layers. **D1 is done; D2 is next.**

#### D1 — API authentication (callers → FastAPI) (Done)

Protect mission/crew routes so anonymous internet traffic cannot read/write prod data through the API.

**What shipped:**

| Piece | Location |
|-------|----------|
| Dependency | [`src/auth.py`](../src/auth.py) — `APIKeyHeader(name="X-API-KEY")` + `get_api_key` |
| Applied on router | [`src/routers.py`](../src/routers.py) — `dependencies=[Depends(get_api_key)]` |
| Left open | `GET /health` on [`src/main.py`](../src/main.py) |
| Local / Azure config | `API_KEY` in `.env` and App Service Environment variables |
| Docs placeholder | `.env.example` includes `API_KEY=your-api-key-here` |
| Tests | [`tests/conftest.py`](../tests/conftest.py) overrides `get_api_key` so existing tests need no header |

```text
Client  --X-API-KEY: <secret>-->  App Service  -->  Postgres
```

Example:

```bash
# 401 without key
curl https://<app-host>/cosmic-missions

# 200 with key
curl https://<app-host>/cosmic-missions -H "X-API-KEY: $API_KEY"
```

Optional stretch: dedicated unit tests for missing/wrong key → `401`.

#### D2 — Database authentication (App Service → Postgres) (Done — code path)

App Service uses **system-assigned Managed Identity** to get an Entra token; Postgres role `rg-cosmic-missions` was granted CONNECT + CRUD.

**What shipped:**

| Piece | Detail |
|-------|--------|
| Web App identity | System-assigned On |
| Postgres | Entra + password auth; Entra admin set; role `rg-cosmic-missions` + grants |
| Code | [`src/database.py`](../src/database.py) — if `DATABASE_URL` set → password (local/CI); else `DBHOST`/`DBNAME`/`DBUSER` + `DefaultAzureCredential` |
| Azure env | `DBHOST`, `DBNAME`, `DBUSER=rg-cosmic-missions`; leave `DATABASE_URL` **unset** on App Service |
| Local | Keep `DATABASE_URL` in `.env` (Docker password) |

```text
App Service (Managed Identity)  --Entra token-->  Flexible Server (role rg-cosmic-missions)
```

Optional stretch: switch Postgres to **Entra authentication only** after confirming MI works; Key Vault for `API_KEY`.

Never commit API keys or DB passwords. Rotate anything that appeared in chat, screenshots, or shared docs.

---

---

### Phase E — CI/CD deploy (Done)

**Done:**

- `.github/workflows/main_rg-cosmic-missions.yml` builds and deploys to App Service on push to `main` (OIDC) or `workflow_dispatch`
- Deploy is gated: `test` job calls reusable `.github/workflows/test.yml`, then `deploy: needs: [build, test]` so broken tests never ship
- `TEST_DATABASE_URL` stays in the **test** workflow only (CI Postgres) — pytest never points at Azure prod

```text
push to main → test (reusable test.yml) + build → deploy (only if both succeed)
```

---

### Phase F — Learn Terraform (reproduce the stack as code)

After you can click the stack together in Portal and tear it down, encode it so recreate is one command.

Suggested layout:

```text
infra/
  providers.tf      # azurerm + backend
  variables.tf      # names, SKU, location
  main.tf           # resource group, Flexible Server, database, App Service plan, Web App
  outputs.tf        # app hostname, Postgres FQDN
```

Learning sequence:

1. Install Terraform; `az login`; create a small `azurerm` provider config
2. Import or recreate: resource group → Flexible Server → database → App Service plan → Web App
3. Wire app settings (`DATABASE_URL` or identity-related settings) via Terraform — prefer variables/secrets, not hardcoded values in `.tf` files
4. `terraform plan` / `apply` / `destroy` against a throwaway resource group until the loop feels safe
5. Optional stretch: remote state in Azure Storage; GitHub Actions job that runs `terraform plan` on PRs

What Terraform is teaching: the Portal clicks were the mental model; HCL is the reproducible version. Do **not** start with Terraform before Phase C — you want one working reference deployment to compare against.

---

### Environment separation (important)

| Environment | Database | Auth | Where config lives |
|-------------|----------|------|-------------------|
| Local dev | Docker `fastapi_postgres_db` | Optional / disabled API key | `.env` (gitignored) |
| CI / pytest | Ephemeral Postgres in GitHub Actions | Dependency override / no prod key | Workflow `env:` |
| Azure prod | Flexible Server | API key for callers; password URL then Managed Identity for DB | App Service settings / Key Vault / identity |

Never point pytest at production Azure Postgres. Rollback fixtures assume a disposable test database.

---

### Connection string and startup notes

Local `.env` today:

```text
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/cosmic_missions_db
```

Azure (password + SSL, early phases):

```text
postgresql://<user>@<server>.postgres.database.azure.com:5432/cosmic_missions_db?sslmode=require
```

Startup (with `PYTHONPATH=src`):

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

App Service may set `PORT` — some teams use `--port ${PORT:-8000}`.

Verify locally before deploying:

```bash
cd src
uvicorn main:app --reload
```

---

### Common gotchas

| Problem | Likely cause |
|---------|----------------|
| App starts but all DB calls fail | Wrong `DATABASE_URL`, missing `sslmode=require`, or firewall blocking App Service |
| `502 Bad Gateway` | `uvicorn` not binding to `0.0.0.0`, wrong startup command, crash on import, or missing `PYTHONPATH=src` |
| Works locally, fails in Azure | `.env` not deployed (it shouldn't be) — setting missing in App Service config |
| Migrations / empty tables | Both create-table SQL files not run on Azure DB yet |
| Prod returns 401 on all mission routes | `API_KEY` missing in Azure Environment variables, or auth code not deployed |
| Identity connect fails after D2 | AAD admin not set on Flexible Server, role missing, or token/driver wiring incomplete |
| Terraform drifts from Portal | Manual Portal edits after `apply` — either import changes or stop clicking outside Terraform |
| Slow cold starts | Normal on free/low tiers; upgrade plan or enable Always On (paid tiers) |

---

### Effort estimate: L (large)

Mostly portal/CLI wiring, networking, auth, CI, and IaC — not large Python rewrites. Budget time for firewall rules, SSL, first deploy debugging, then identity + Terraform as separate learning chunks.

### Immediate next actions

1. ~~Phases 0–E~~ (done — deploy gated on reusable test workflow)
2. Confirm live API after deploy (`/health` + keyed `/cosmic-missions`)
3. Point local `.env` `DATABASE_URL` at Docker when not cloud-testing
4. Stop Azure Postgres when idle to control cost
5. **Phase F:** encode stack in `infra/` with Terraform

### Optional stretch goals

- **Staging slot** on App Service — deploy to staging, swap after smoke tests
- **Private networking** — VNet-integrate App Service and Postgres (no public DB endpoint)
- **App Service Easy Auth** (Microsoft Entra ID) instead of a shared API key
- **Remote Terraform state** + PR `terraform plan` in CI
- **Application Insights** for request tracing

---

## References

- FastAPI [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- FastAPI [Testing Dependencies](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- FastAPI [Security — First Steps](https://fastapi.tiangolo.com/tutorial/security/first-steps/)
- Python [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- pytest [Monkeypatching / mocker](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) (or [`pytest-mock`](https://pytest-mock.readthedocs.io/))
- SQLAlchemy [Relationship Configuration](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)
- PostgreSQL [Foreign Keys](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK)
- Azure [App Service — Deploy Python](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python)
- Azure [Database for PostgreSQL Flexible Server](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/overview)
- Azure [Configure Python apps](https://learn.microsoft.com/en-us/azure/app-service/configure-language-python)
- Azure [Managed Identity overview](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview)
- Azure [PostgreSQL Flexible Server — Microsoft Entra authentication](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-configure-sign-in-azure-ad-authentication)
- Terraform [AzureRM provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- HashiCorp [Terraform Azure get started](https://developer.hashicorp.com/terraform/tutorials/azure-get-started)
- [api-testing-checklist.md](api-testing-checklist.md) — pytest patterns you already use
