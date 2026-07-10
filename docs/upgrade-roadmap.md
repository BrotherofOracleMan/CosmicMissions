# Upgrade Roadmap: APIRouter + Test Suite

A learning-focused guide and next steps for this project. Companion to [api-testing-checklist.md](api-testing-checklist.md).

You have a solid baseline: cosmic missions CRUD API, pytest coverage across HTTP methods, an `APIRouter` refactor, an isolated test database, per-test transaction rollback, test markers, coverage reporting, and GitHub Actions CI. The long-term goal is deploying this stack to **Azure** — this doc explains what changed, why it helps, and what to tackle next.

---

## Part 1: API structure with `APIRouter`

### Current structure (done)

Routes are split between a thin app entry point and a dedicated router module:

```
src/
  main.py       # FastAPI app, include_router
  routers.py    # all /cosmic-missions routes
  database.py
  models.py
  schemas.py
```

**`main.py`** wires the app:

```python
app = FastAPI()
app.include_router(cosmic_missions_router)
```

**`routers.py`** owns the feature:

- `router = APIRouter(prefix="/cosmic-missions", tags=["cosmic-missions"])`
- All GET, POST, PUT, PATCH, DELETE handlers
- Same `Depends(get_db)` pattern as before — no behavior change

Route decorators use paths relative to the prefix: `@router.get("")`, `@router.get("/success")`, `@router.get("/{mission_id}")`, etc. Client URLs stay the same (`/cosmic-missions`, `/cosmic-missions/success`, …).

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

- **39 tests** across 7 files by HTTP concern: post, get, put, patch, delete, roundtrip, database
- Tests use **real PostgreSQL**, but now through a dedicated test database: `cosmic_missions_test_db`
- `tests/conftest.py` owns shared pytest setup: `db_session`, `client_with_rollback`, dependency override, per-test transaction rollback, and reusable data fixtures
- `tests/payloads/missions.py` owns reusable mission payloads and shared test IDs
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

`.github/workflows/test.yml` runs the full suite on every push to `main` via a Postgres service container.

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
| CI automation | GitHub Actions runs `pytest` on push to `main` with ephemeral Postgres |

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
- `cosmic_missions` table exists in the test database
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
- `ROUNDTRIP_CREATE`, `ROUNDTRIP_PATCH`, `ROUNDTRIP_PUT`

`tests/assertions.py` now holds:

- `verify_mission_fields()`
- `verify_path_int_parsing_error()`

### Other pytest upgrades (optional next steps)

Markers, coverage, and CI are done. Remaining ideas:

1. **`pytest.mark.parametrize` expansion** — same pattern for PATCH/PUT invalid bodies
2. **`pytest.raises` / error helpers** — useful if you add service-layer unit tests
3. **Factory helpers** — `make_mission_payload(**overrides)` if static payloads feel rigid
4. **HTTP status polish** — assert `201` on POST if you change the API
5. **CI enhancements** — add `pull_request` trigger, `--cov=src` in the workflow, or split unit/integration jobs

### What to keep from your current suite

- File-per-HTTP-method layout — still readable
- Explicit assertions (no over-abstracted helpers) — good for learning
- Roundtrip file — becomes even more valuable with isolated DB
- Parametrize for validation errors — keep expanding, not replacing

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
    ci --> fkeys[Foreign keys + related tables]
    fkeys --> azure[Deploy to Azure]
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
| 8 | Foreign keys and related tables | M–L | Next |
| 9 | Deploy to Azure | L | Final |

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

All 39 tests use `client_with_rollback`. The old `client` fixture and `get_test_db` helper were removed.

### Clearing a dirty test DB (one-time recovery)

If you ran tests before rollback was fully wired, leftover rows may still exist in `cosmic_missions_test_db`. Truncate via Docker:

```bash
docker exec -it fastapi_postgres_db psql -U postgres -d cosmic_missions_test_db -c \
  "TRUNCATE TABLE cosmic_missions;"
```

After rollback is in place, you should not need this routinely.

---

## Step 7: Markers, coverage, CI (Done)

Step 7 made the suite faster to run in subsets, measurable with coverage, and automatic on every push to `main`.

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
| `integration` | 22 | CRUD, 404 lookups, 409 duplicate, roundtrip |
| `unit` | 15 | invalid path param (`/abc`), parametrized POST 422s |

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

Current baseline: **100% line coverage** on `src/` (39 tests). `database.py` is covered via `tests/test_database.py`, which exercises the real `get_db()` generator.

Coverage is a guide, not a goal by itself — use it to spot untested branches after refactors.

### Part C: CI pipeline — GitHub Actions (done)

Workflow file: `.github/workflows/test.yml`

```mermaid
flowchart LR
    push[Push to main] --> gha[GitHub Actions ubuntu-latest]
    gha --> pg[(Postgres 15 service container)]
    gha --> setup[uv sync + psql create DB/table]
    setup --> pytest[uv run pytest]
    pytest --> result[Pass or fail on Actions tab]
```

What the workflow does on each push to `main`:

1. Starts a `postgres:15` service container with health checks
2. Sets `DATABASE_URL` and `TEST_DATABASE_URL` to the CI test database
3. Checks out code, installs `uv`, runs `uv sync`
4. Installs `postgresql-client`, creates `cosmic_missions_test_db`, runs `sql_files/create_cosmic_missions_table.sql`
5. Runs `uv run pytest` (all 39 tests)

View results: GitHub repo → **Actions** tab, or locally with `gh run list` / `gh run view --log`.

```text
Local (your Mac)          CI (GitHub runner)
─────────────────         ──────────────────
Docker Postgres           Postgres service container
.env credentials          workflow env: block
You run pytest            Runs on push to main
```

### Optional CI enhancements (not implemented)

- Add `pull_request:` trigger so PRs run tests before merge
- Add `pytest --cov=src` to the workflow
- Split into separate unit and integration jobs

---

## Step 8: Foreign keys and related tables (Next)

Right now you have a **single table** — `cosmic_missions` with no relationships. That is a fine starting point. The next natural schema lesson is adding a **child table** linked by a foreign key.

### Why learn foreign keys here

Your API already has concepts that imply relationships:

- `crew_size` on a mission — but no actual crew member rows
- `telemetry_data` as JSONB — flexible, but not queryable as structured rows

A child table makes the database enforce **referential integrity**: you cannot point at a mission that does not exist.

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

### A concrete example: `crew_members`

**SQL** (new migration file alongside `create_cosmic_missions_table.sql`):

```sql
CREATE TABLE crew_members (
    crew_member_id  SERIAL PRIMARY KEY,
    mission_id      INTEGER NOT NULL
                    REFERENCES cosmic_missions(mission_id)
                    ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    role            VARCHAR(100) NOT NULL
);
```

**SQLAlchemy model** (sketch):

```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

class CrewMember(Base):
    __tablename__ = "crew_members"

    crew_member_id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("cosmic_missions.mission_id"))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(100))

    mission: Mapped["CosmicMission"] = relationship(back_populates="crew_members")

class CosmicMission(Base):
    # ... existing columns ...
    crew_members: Mapped[list["CrewMember"]] = relationship(back_populates="mission")
```

### `ON DELETE` behavior — pick deliberately

| Option | What happens when parent mission is deleted | Good for |
|--------|---------------------------------------------|----------|
| `CASCADE` | Child crew rows deleted automatically | Owned children (crew belongs to one mission) |
| `RESTRICT` | Delete blocked if children exist | When orphans must never happen |
| `SET NULL` | Child `mission_id` set to `NULL` (column must be nullable) | Optional relationships |

Your current `DELETE /cosmic-missions/{id}` would behave differently depending on this choice — worth testing explicitly.

### API design options

Nested routes fit parent/child well:

| Route | Purpose |
|-------|---------|
| `POST /cosmic-missions/{mission_id}/crew` | Add crew member to existing mission |
| `GET /cosmic-missions/{mission_id}/crew` | List crew for a mission |
| `DELETE /cosmic-missions/{mission_id}/crew/{crew_member_id}` | Remove one crew member |

New error paths to handle and test:

| Scenario | Likely response |
|----------|-----------------|
| POST crew for missing `mission_id` | `404` — mission not found (check parent first) |
| POST crew with invalid body | `422` — Pydantic validation |
| DB FK violation if you skip the parent check | `409` or `500` — handle `IntegrityError` like duplicate POST |

Pattern you already use on POST:

```python
try:
    db.commit()
except IntegrityError:
    db.rollback()
    raise HTTPException(status_code=409, detail="...")
```

### What changes in tests

Your rollback setup still works — FK constraints apply **inside** the test transaction.

Fixture order matters more:

```text
apollo_11_mission fixture  → creates parent mission
crew_member fixture        → POST child row referencing mission_id 1
test                       → GET nested route, assert crew list
rollback                   → both parent and child disappear
```

Tests worth adding:

1. **Happy path** — create mission, add crew, GET crew list returns expected rows
2. **Orphan FK** — POST crew for `mission_id=999999` → `404` (if you validate parent in the route)
3. **Cascade delete** — DELETE mission → follow-up GET crew returns `404` or empty list
4. **Restrict delete** — if using `ON DELETE RESTRICT`, DELETE mission with crew → `409` or `400`

Payload fixtures would grow (`CREW_MEMBER_APOLLO`, etc.) — same pattern as `tests/payloads/missions.py`.

### Suggested learning path for Step 8

1. Read PostgreSQL docs on [foreign keys](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK) and `ON DELETE` options
2. Create `sql_files/create_crew_members_table.sql` and run it on dev + test DBs
3. Add `CrewMember` model + `relationship()` on `CosmicMission`
4. Add Pydantic schemas (`CrewMemberCreate`, `CrewMemberBase`)
5. Add nested routes in `routers.py` (or a new router file)
6. Add fixtures: parent mission first, then crew member
7. Test FK error paths and cascade/restrict delete behavior
8. Update CI workflow to create both tables

### Effort estimate: M–L (medium to large)

Touches SQL, models, schemas, routes, and tests — but each piece reuses patterns you already know. Good capstone after rollback and CI.

### Optional stretch goals

- Eager-load crew with missions: `db.query(CosmicMission).options(joinedload(CosmicMission.crew_members))`
- Alembic migrations instead of raw SQL files
- Replace `telemetry_data` JSONB with a `telemetry_events` child table (queryable history)

---

## Step 9: Deploy to Azure (Final)

Move from **local Docker Postgres + uvicorn on your machine** to a hosted FastAPI API and managed PostgreSQL in Azure. Your app already reads `DATABASE_URL` from the environment — that pattern maps directly to Azure App Settings.

### Target architecture

```mermaid
flowchart LR
    client[API clients / browser] --> app[Azure App Service Linux]
    app --> pg[(Azure Database for PostgreSQL Flexible Server)]
    gh[GitHub Actions] -->|deploy on push| app
    gh -->|pytest in CI| testPg[(Postgres service container)]
```

| Local (today) | Azure (target) |
|---------------|----------------|
| Docker `postgres:16` on `localhost:5432` | Azure Database for PostgreSQL — Flexible Server |
| `uvicorn` run manually | Azure App Service (Linux) or Container Apps |
| `.env` file on your Mac | App Service **Configuration** / Key Vault references |
| `cosmic_missions_db` | Production database on Flexible Server |
| `cosmic_missions_test_db` | Stays in **CI only** — not required in Azure prod |

**Why Flexible Server:** you already use PostgreSQL, `psycopg2`, and JSONB (`telemetry_data`). Azure's managed Postgres is the closest lift — no database rewrite.

**Why App Service (Linux):** simplest path for a FastAPI app with `uvicorn`. Container Apps is a good alternative if you prefer shipping a Docker image (similar to your local Postgres container mental model).

### What you need in Azure

1. **Resource group** — e.g. `rg-cosmic-missions`
2. **PostgreSQL Flexible Server** — e.g. `cosmic-missions-pg`
3. **Database** — e.g. `cosmic_missions_db` (run `sql_files/create_cosmic_missions_table.sql`)
4. **App Service plan** — Linux, Python 3.13 (or container if using Docker)
5. **Web App** — e.g. `cosmic-missions-api`

Optional but recommended:

- **GitHub Actions** deploy workflow (extends the existing test workflow in Step 7)
- **Application Insights** for logs and request tracing
- **Key Vault** for `DATABASE_URL` instead of plain app settings

### Connection string changes

Local `.env` today:

```text
DATABASE_URL=postgresql://postgres:2421@localhost:5432/cosmic_missions_db
```

Azure Postgres typically requires **SSL**. Your SQLAlchemy URL becomes something like:

```text
postgresql://<user>@<server>.postgres.database.azure.com:5432/cosmic_missions_db?sslmode=require
```

Notes:

- Azure Flexible Server usernames are often `adminuser@servername` format
- Store the full URL in App Service **Configuration → Application settings** as `DATABASE_URL` — never commit it
- `database.py` already uses `os.getenv("DATABASE_URL")` — no code change required for basic deploy
- Firewall: allow your dev IP while testing; enable **Allow public access from Azure services** for App Service → DB traffic

### App startup

App Service needs a startup command. From `src/` as the working directory (match your `pythonpath` layout):

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

App Service sets `PORT` — some teams use:

```bash
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Verify locally before deploying:

```bash
cd src
uvicorn main:app --reload
```

### Suggested learning path for Step 9

**Phase A — Database**

1. Create a PostgreSQL Flexible Server in the [Azure portal](https://portal.azure.com) (or `az postgres flexible-server create`)
2. Create database `cosmic_missions_db`
3. Run `sql_files/create_cosmic_missions_table.sql` against the Azure server (psql or Azure Cloud Shell)
4. Test connection from your Mac with `DATABASE_URL` + `sslmode=require` before deploying the app

**Phase B — App**

5. Create Linux App Service plan + Web App (Python 3.13)
6. Set `DATABASE_URL` in Application settings
7. Configure startup command for `uvicorn`
8. Deploy code — options (pick one to learn):
   - **GitHub Actions** → `azure/webapps-deploy` (best long-term; pairs with Step 7)
   - **ZIP deploy** from CLI (`az webapp up`) for a first manual deploy
   - **Docker** → push to Azure Container Registry → App Service or Container Apps

**Phase C — Verify**

9. Hit `https://<your-app>.azurewebsites.net/docs` — Swagger UI should load
10. `POST /cosmic-missions` with a test payload; `GET /cosmic-missions` confirms DB wiring
11. Add a simple `GET /health` route (optional) for App Service health checks

**Phase D — CI/CD**

12. Extend GitHub Actions: add a deploy job (only on `main`) alongside the existing test job
13. Keep `TEST_DATABASE_URL` in the **test** job only — production Azure DB is not your test DB

### Environment separation (important)

| Environment | Database | Where config lives |
|-------------|----------|-------------------|
| Local dev | Docker `fastapi_postgres_db` | `.env` (gitignored) |
| CI / pytest | Ephemeral Postgres in GitHub Actions | Workflow `env:` |
| Azure prod | Flexible Server | App Service settings / Key Vault |

Never point pytest at production Azure Postgres. Your rollback fixtures assume a disposable test database.

### Code / repo prep (before first deploy)

| Task | Why |
|------|-----|
| Add `.gitignore` entries for `.env`, `.venv` | Secrets and local tooling stay local |
| Add `requirements.txt` or ensure `pyproject.toml` is installable in App Service | Azure build needs dependency list |
| Consider `GET /health` | App Service can probe liveness |
| Remove hardcoded local passwords from any docs you share publicly | Rotate credentials if exposed |

No API behavior change is required for a basic deploy — your router, schemas, and `get_db` pattern are already cloud-friendly.

### Common gotchas

| Problem | Likely cause |
|---------|----------------|
| App starts but all DB calls fail | Wrong `DATABASE_URL`, missing `sslmode=require`, or firewall blocking App Service |
| `502 Bad Gateway` | `uvicorn` not binding to `0.0.0.0`, wrong startup command, or crash on import |
| Works locally, fails in Azure | `.env` not deployed (it shouldn't be) — setting missing in App Service config |
| Migrations / empty tables | `create_cosmic_missions_table.sql` not run on Azure DB yet |
| Slow cold starts | Normal on free/low tiers; upgrade plan or enable Always On (paid tiers) |

### Effort estimate: L (large)

Mostly portal/CLI wiring, networking, and CI — not Python rewrites. Budget time for firewall rules, SSL connection strings, and first deploy debugging.

### Optional stretch goals

- **Staging slot** on App Service — deploy `main` to staging, swap to production after smoke tests
- **Private networking** — VNet-integrate App Service and Postgres (no public DB endpoint)
- **Managed identity** instead of password in `DATABASE_URL`
- **Bicep / Terraform** to reproduce the whole stack as code

---

## References

- FastAPI [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- FastAPI [Testing Dependencies](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- SQLAlchemy [Relationship Configuration](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)
- PostgreSQL [Foreign Keys](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK)
- Azure [App Service — Deploy Python](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python)
- Azure [Database for PostgreSQL Flexible Server](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/overview)
- Azure [Configure Python apps](https://learn.microsoft.com/en-us/azure/app-service/configure-language-python)
- [api-testing-checklist.md](api-testing-checklist.md) — pytest patterns you already use
