"""Test cases for PUT /cosmic-missions/{id} — full replace (send all fields)."""
import pytest

from assertions import verify_mission_fields, verify_path_int_parsing_error
from payloads.missions import FULL_PUT_UPDATE, MISSING_MISSION_ID


@pytest.mark.integration
def test_update_cosmic_mission_success(client_with_rollback, created_mission):
    expected = {"mission_id": created_mission, **FULL_PUT_UPDATE}

    response = client_with_rollback.put(f"/cosmic-missions/{created_mission}", json=FULL_PUT_UPDATE)
    assert response.status_code == 200
    verify_mission_fields(response.json(), expected)

    get_response = client_with_rollback.get(f"/cosmic-missions/{created_mission}")
    assert get_response.status_code == 200
    verify_mission_fields(get_response.json(), expected)


@pytest.mark.integration
def test_update_non_existent_cosmic_mission_failure(client_with_rollback):
    response = client_with_rollback.put(f"/cosmic-missions/{MISSING_MISSION_ID}", json=FULL_PUT_UPDATE)
    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"


@pytest.mark.unit
def test_update_cosmic_mission_with_invalid_path_parameter(client_with_rollback):
    response = client_with_rollback.put("/cosmic-missions/abc", json=FULL_PUT_UPDATE)
    assert response.status_code == 422
    verify_path_int_parsing_error(response)


@pytest.mark.unit
def test_update_cosmic_mission_missing_required_field(client_with_rollback):
    response = client_with_rollback.put(f"/cosmic-missions/{MISSING_MISSION_ID}", json={
        "destination": "Mars",
        "launch_date": "2026-06-24",
        "crew_size": 2,
        "budget_billions": 8000,
        "is_successful": False,
        "telemetry_data": {"test": "updated test"},
    })
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", "mission_name"]
    assert response.json()["detail"][0]["msg"] == "Field required"


@pytest.mark.integration
def test_update_cosmic_mission_with_null_telemetry(client_with_rollback, created_mission):
    response = client_with_rollback.put(
        f"/cosmic-missions/{created_mission}",
        json={**FULL_PUT_UPDATE, "telemetry_data": None},
    )
    assert response.status_code == 200
    assert response.json()["telemetry_data"] is None

    get_response = client_with_rollback.get(f"/cosmic-missions/{created_mission}/telemetry")
    assert get_response.status_code == 200
    assert get_response.json() is None
