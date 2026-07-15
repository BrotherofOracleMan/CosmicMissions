import os
from collections.abc import Generator
from decimal import Decimal

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import get_db
from main import app
from payloads.missions import (
    APOLLO_11,
    MISSION_WITH_CREW_SIZE_ZERO,
    BASE_MISSION,
    DUPLICATE_TEST_MISSION,
    MINIMAL_MISSION,
    NULL_TELEMETRY_MISSION,
    SUCCESSFUL_MISSION,
    TEST_MISSION_ID,
    UNSUCCESSFUL_MISSION,
    CREW_MEMBER_1,
    CREW_MEMBER_2,
)

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

engine = create_engine(TEST_DATABASE_URL)
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

@pytest.fixture
def apollo_11_mission(client_with_rollback: TestClient) -> Generator[dict, None, None]:
    response = client_with_rollback.post("/cosmic-missions", json=APOLLO_11)
    assert response.status_code == 200
    yield APOLLO_11


@pytest.fixture
def test_mission(client_with_rollback: TestClient) -> Generator[dict, None, None]:
    response = client_with_rollback.post("/cosmic-missions", json=DUPLICATE_TEST_MISSION)
    assert response.status_code == 200
    mission = response.json()
    yield mission

@pytest.fixture
def successful_and_unsuccessful_missions(client_with_rollback: TestClient) -> Generator[list[dict], None, None]:
    payloads = [SUCCESSFUL_MISSION, UNSUCCESSFUL_MISSION]
    for payload in payloads:
        response = client_with_rollback.post("/cosmic-missions", json=payload)
        assert response.status_code == 200
    yield payloads
    
@pytest.fixture
def mission_with_null_telemetry(client_with_rollback: TestClient) -> Generator[int, None, None]:
    response = client_with_rollback.post("/cosmic-missions", json=NULL_TELEMETRY_MISSION)
    assert response.status_code == 200
    yield TEST_MISSION_ID
   

@pytest.fixture
def created_mission(client_with_rollback: TestClient) -> Generator[int, None, None]:
    response = client_with_rollback.post("/cosmic-missions", json={
        "mission_id": TEST_MISSION_ID,
        **BASE_MISSION,
    })
    assert response.status_code == 200
    mission_id = response.json()["mission_id"]
    yield mission_id

@pytest.fixture
def created_minimal_mission(client_with_rollback: TestClient) -> Generator[int, None, None]:
    response = client_with_rollback.post("/cosmic-missions", json=MINIMAL_MISSION)
    assert response.status_code == 200
    data = response.json()
    assert data["mission_id"] == TEST_MISSION_ID
    assert data["crew_size"] == 0
    assert Decimal(data["budget_billions"]) == Decimal("0.00")
    assert data["is_successful"] is False
    assert data["telemetry_data"] is None
    mission_id = data["mission_id"]
    yield mission_id

@pytest.fixture
def crew_member_1(
    client_with_rollback: TestClient, apollo_11_mission: dict
) -> Generator[dict, None, None]:
    response = client_with_rollback.post(
        f"/cosmic-missions/{apollo_11_mission['mission_id']}/crew",
        json=CREW_MEMBER_1,
    )
    assert response.status_code == 200
    yield response.json()


@pytest.fixture
def crew_member_2(
    client_with_rollback: TestClient, apollo_11_mission: dict
) -> Generator[dict, None, None]:
    response = client_with_rollback.post(
        f"/cosmic-missions/{apollo_11_mission['mission_id']}/crew",
        json=CREW_MEMBER_2,
    )
    assert response.status_code == 200
    yield response.json()


@pytest.fixture
def mission_with_crew(
    apollo_11_mission: dict, crew_member_1: dict, crew_member_2: dict
) -> Generator[dict, None, None]:
    yield {
        "mission": apollo_11_mission,
        "crew": [crew_member_1, crew_member_2],
    }

@pytest.fixture
def mission_with_crew_size_zero(client_with_rollback: TestClient) -> Generator[dict, None, None]:
    response = client_with_rollback.post("/cosmic-missions", json=MISSION_WITH_CREW_SIZE_ZERO)
    assert response.status_code == 200
    yield response.json()