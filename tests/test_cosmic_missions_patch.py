"""Test cases for PATCH /cosmic-missions/{id} — partial update (send only fields to change)."""
from decimal import Decimal

import pytest

from assertions import verify_path_int_parsing_error
from payloads.missions import BASE_MISSION, MISSING_MISSION_ID


@pytest.mark.integration
def test_patch_cosmic_mission_single_field(client_with_rollback, created_mission):
    response = client_with_rollback.patch(
        f"/cosmic-missions/{created_mission}",
        json={"mission_name": "Patched Name Only"},
    )
    assert response.status_code == 200
    assert response.json()["mission_name"] == "Patched Name Only"
    assert response.json()["destination"] == BASE_MISSION["destination"]
    assert response.json()["crew_size"] == BASE_MISSION["crew_size"]
    assert response.json()["telemetry_data"] == BASE_MISSION["telemetry_data"]

    get_response = client_with_rollback.get(f"/cosmic-missions/{created_mission}")
    assert get_response.status_code == 200
    assert get_response.json()["mission_name"] == "Patched Name Only"
    assert get_response.json()["destination"] == BASE_MISSION["destination"]
    assert get_response.json()["launch_date"] == BASE_MISSION["launch_date"]
    assert get_response.json()["crew_size"] == BASE_MISSION["crew_size"]
    assert Decimal(get_response.json()["budget_billions"]) == Decimal("99999.00")
    assert get_response.json()["is_successful"] is True
    assert get_response.json()["telemetry_data"] == BASE_MISSION["telemetry_data"]


@pytest.mark.integration
def test_patch_cosmic_mission_empty_body(client_with_rollback, created_mission):
    response = client_with_rollback.patch(f"/cosmic-missions/{created_mission}", json={})
    assert response.status_code == 200
    assert response.json()["mission_name"] == BASE_MISSION["mission_name"]
    assert response.json()["destination"] == BASE_MISSION["destination"]
    assert response.json()["launch_date"] == BASE_MISSION["launch_date"]
    assert response.json()["crew_size"] == BASE_MISSION["crew_size"]
    assert Decimal(response.json()["budget_billions"]) == Decimal("99999.00")
    assert response.json()["is_successful"] is True
    assert response.json()["telemetry_data"] == BASE_MISSION["telemetry_data"]

    get_response = client_with_rollback.get(f"/cosmic-missions/{created_mission}")
    assert get_response.status_code == 200
    assert get_response.json()["mission_name"] == BASE_MISSION["mission_name"]
    assert get_response.json()["destination"] == BASE_MISSION["destination"]
    assert get_response.json()["launch_date"] == BASE_MISSION["launch_date"]
    assert get_response.json()["crew_size"] == BASE_MISSION["crew_size"]
    assert Decimal(get_response.json()["budget_billions"]) == Decimal("99999.00")
    assert get_response.json()["is_successful"] is True
    assert get_response.json()["telemetry_data"] == BASE_MISSION["telemetry_data"]


@pytest.mark.integration
def test_patch_cosmic_mission_telemetry_data_null(client_with_rollback, created_mission):
    response = client_with_rollback.patch(
        f"/cosmic-missions/{created_mission}",
        json={"telemetry_data": None},
    )
    assert response.status_code == 200
    assert response.json()["telemetry_data"] is None

    get_response = client_with_rollback.get(f"/cosmic-missions/{created_mission}")
    assert get_response.status_code == 200
    assert get_response.json()["telemetry_data"] is None
    assert get_response.json()["mission_name"] == BASE_MISSION["mission_name"]


@pytest.mark.integration
def test_patch_non_existent_cosmic_mission_failure(client_with_rollback):
    response = client_with_rollback.patch(
        f"/cosmic-missions/{MISSING_MISSION_ID}",
        json={"mission_name": "Should Not Work"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"


@pytest.mark.unit
def test_patch_cosmic_mission_with_invalid_path_parameter(client_with_rollback):
    response = client_with_rollback.patch("/cosmic-missions/abc", json={"mission_name": "Should Not Work"})
    assert response.status_code == 422
    verify_path_int_parsing_error(response)


@pytest.mark.unit
def test_patch_cosmic_mission_invalid_body(client_with_rollback, created_mission):
    response = client_with_rollback.patch(
        f"/cosmic-missions/{created_mission}",
        json={"crew_size": "three"},
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "int_parsing"
    assert response.json()["detail"][0]["loc"] == ["body", "crew_size"]
    assert response.json()["detail"][0]["msg"] == "Input should be a valid integer, unable to parse string as an integer"


@pytest.mark.integration
def test_patch_cosmic_mission_budget_billions_only(client_with_rollback, created_mission):
    response = client_with_rollback.patch(
        f"/cosmic-missions/{created_mission}",
        json={"budget_billions": 42.50},
    )
    assert response.status_code == 200
    assert Decimal(response.json()["budget_billions"]) == Decimal("42.50")
    assert response.json()["mission_name"] == BASE_MISSION["mission_name"]

    get_response = client_with_rollback.get(f"/cosmic-missions/{created_mission}")
    assert get_response.status_code == 200
    assert Decimal(get_response.json()["budget_billions"]) == Decimal("42.50")

@pytest.mark.integration
def test_patch_cosmic_mission_with_destination_launch_date_crew_size(client_with_rollback, created_mission):
    response = client_with_rollback.patch(
        f"/cosmic-missions/{created_mission}",
        json={"destination": "Jupiter", "launch_date": "2026-08-01", "crew_size": 10},
    )
    assert response.status_code == 200
    assert response.json()["destination"] == "Jupiter"
    assert response.json()["launch_date"] == "2026-08-01"
    assert response.json()["crew_size"] == 10
    assert response.json()["mission_name"] == BASE_MISSION["mission_name"]

    get_response = client_with_rollback.get(f"/cosmic-missions/{created_mission}")
    assert get_response.status_code == 200
    assert get_response.json()["destination"] == "Jupiter"
    assert get_response.json()["launch_date"] == "2026-08-01"
    assert get_response.json()["crew_size"] == 10
    assert get_response.json()["mission_name"] == BASE_MISSION["mission_name"]
