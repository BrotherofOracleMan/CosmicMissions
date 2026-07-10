from decimal import Decimal

import pytest

from payloads.missions import TEST_MISSION_ID

INVALID_BODY_CASES = [
    pytest.param(
        {"mission_name": "Test Mission", "destination": "Mars"},
        422, "mission_id", "missing", "Field required",
        id="missing_mission_id",
    ),
    pytest.param(
        {"mission_id": 99994, "destination": "Mars"},
        422, "mission_name", "missing", "Field required",
        id="missing_mission_name",
    ),
    pytest.param(
        {"mission_id": 99994, "mission_name": "Test Mission"},
        422, "destination", "missing", "Field required",
        id="missing_destination",
    ),
    pytest.param(
        {"mission_id": "abc", "mission_name": "Test Mission", "destination": "Mars"},
        422, "mission_id", "int_parsing",
        "Input should be a valid integer, unable to parse string as an integer",
        id="invalid_mission_id_type",
    ),
    pytest.param(
        {"mission_id": 99994, "mission_name": "Test Mission", "destination": "Mars", "launch_date": "06-23-2026"},
        422, "launch_date", "date_from_datetime_parsing",
        "Input should be a valid date or datetime, invalid character in year",
        id="invalid_launch_date",
    ),
    pytest.param(
        {"mission_id": 99994, "mission_name": "Test Mission", "destination": "Mars", "crew_size": "three"},
        422, "crew_size", "int_parsing",
        "Input should be a valid integer, unable to parse string as an integer",
        id="invalid_crew_size_type",
    ),
    pytest.param(
        {"mission_id": 99994, "mission_name": "Test Mission", "destination": "Mars", "is_successful": "maybe"},
        422, "is_successful", "bool_parsing",
        "Input should be a valid boolean, unable to interpret input",
        id="invalid_is_successful_type",
    ),
    pytest.param(
        {"mission_id": 99994, "mission_name": "Test Mission", "destination": "Mars", "telemetry_data": "not-a-dict"},
        422, "telemetry_data", "dict_type", "Input should be a valid dictionary",
        id="invalid_telemetry_data_type",
    ),
]


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload, expected_status_code, field, error_type, error_msg",
    INVALID_BODY_CASES,
)
def test_invalid_fields_in_request_body(client_with_rollback, payload, expected_status_code, field, error_type, error_msg):
    response = client_with_rollback.post("/cosmic-missions", json=payload)
    assert response.status_code == expected_status_code
    assert response.json()["detail"][0]["type"] == error_type
    assert response.json()["detail"][0]["loc"] == ["body", field]
    assert response.json()["detail"][0]["msg"] == error_msg


@pytest.mark.integration
def test_create_cosmic_mission_with_required_fields_only(client_with_rollback):
    create_response = client_with_rollback.post("/cosmic-missions", json={
        "mission_id": TEST_MISSION_ID,
        "mission_name": "Minimal Mission",
        "destination": "Mars",
    })
    assert create_response.status_code == 200
    assert create_response.json()["mission_id"] == TEST_MISSION_ID
    assert create_response.json()["mission_name"] == "Minimal Mission"
    assert create_response.json()["destination"] == "Mars"
    assert create_response.json()["crew_size"] == 0
    assert Decimal(create_response.json()["budget_billions"]) == Decimal("0.00")
    assert create_response.json()["is_successful"] is False
    assert create_response.json()["telemetry_data"] is None

    delete_response = client_with_rollback.delete(f"/cosmic-missions/{TEST_MISSION_ID}")
    assert delete_response.status_code == 200


@pytest.mark.integration
def test_create_cosmic_mission_with_null_telemetry(client_with_rollback):
    create_response = client_with_rollback.post("/cosmic-missions", json={
        "mission_id": TEST_MISSION_ID,
        "mission_name": "Null Telemetry Mission",
        "destination": "Mars",
        "telemetry_data": None,
    })
    assert create_response.status_code == 200
    assert create_response.json()["telemetry_data"] is None

    telemetry_response = client_with_rollback.get(f"/cosmic-missions/{TEST_MISSION_ID}/telemetry")
    assert telemetry_response.status_code == 200
    assert telemetry_response.json() is None

    delete_response = client_with_rollback.delete(f"/cosmic-missions/{TEST_MISSION_ID}")
    assert delete_response.status_code == 200


@pytest.mark.integration
def test_create_cosmic_mission_duplicate_id(client_with_rollback, test_mission):
    response = client_with_rollback.post("/cosmic-missions", json={
        "mission_id": test_mission["mission_id"],
        "mission_name": test_mission["mission_name"],
        "destination": test_mission["destination"],
        "launch_date": test_mission["launch_date"],
        "crew_size": test_mission["crew_size"],
        "budget_billions": test_mission["budget_billions"],
        "is_successful": test_mission["is_successful"],
        "telemetry_data": test_mission["telemetry_data"],
    })
    assert response.status_code == 409
    assert response.json()["detail"] == "Mission with this ID already exists"
