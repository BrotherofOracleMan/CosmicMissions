import pytest
from assertions import verify_mission_fields, verify_path_int_parsing_error
from payloads.missions import EXPECTED_MISSION_KEYS, MISSING_MISSION_ID

@pytest.mark.integration
def test_get_cosmic_missions(client_with_rollback, apollo_11_mission):
    response = client_with_rollback.get("/cosmic-missions")
    assert response.status_code == 200

    missions = response.json()
    assert isinstance(missions, list)
    assert len(missions) > 0
    assert EXPECTED_MISSION_KEYS.issubset(missions[0].keys())
    verify_mission_fields(missions[0], apollo_11_mission)
    assert isinstance(missions[0]["telemetry_data"], dict)

@pytest.mark.integration
def test_get_cosmic_mission_by_id(client_with_rollback, apollo_11_mission):
    response = client_with_rollback.get(f"/cosmic-missions/{apollo_11_mission['mission_id']}")
    assert response.status_code == 200
    verify_mission_fields(response.json(), apollo_11_mission)
    assert isinstance(response.json()["telemetry_data"], dict)


@pytest.mark.integration
def test_get_cosmic_mission_by_mission_id_failure(client_with_rollback):
    response = client_with_rollback.get(f"/cosmic-missions/{MISSING_MISSION_ID}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"


@pytest.mark.unit
def test_get_cosmic_mission_by_invalid_mission_id_type(client_with_rollback):
    response = client_with_rollback.get("/cosmic-missions/abc")
    assert response.status_code == 422
    verify_path_int_parsing_error(response)


@pytest.mark.integration
def test_get_all_successful_missions(client_with_rollback, successful_and_unsuccessful_missions):
    response = client_with_rollback.get("/cosmic-missions/success")
    assert response.status_code == 200

    missions = response.json()
    assert isinstance(missions, list)
    assert len(missions) == 1
    assert missions[0]["is_successful"] is True
    assert EXPECTED_MISSION_KEYS.issubset(missions[0].keys())
    verify_mission_fields(missions[0], successful_and_unsuccessful_missions[0])


@pytest.mark.integration
def test_get_cosmic_mission_telemetry_data_by_mission_id(client_with_rollback, apollo_11_mission):
    response = client_with_rollback.get(f"/cosmic-missions/{apollo_11_mission['mission_id']}/telemetry")
    assert response.status_code == 200
    assert response.json() == apollo_11_mission["telemetry_data"]

@pytest.mark.integration
def test_get_cosmic_mission_telemetry_data_null(client_with_rollback, mission_with_null_telemetry):
    response = client_with_rollback.get(f"/cosmic-missions/{mission_with_null_telemetry}/telemetry")
    assert response.status_code == 200
    assert response.json() is None

@pytest.mark.integration
def test_get_cosmic_mission_telemetry_data_by_mission_id_failure(client_with_rollback):
    response = client_with_rollback.get(f"/cosmic-missions/{MISSING_MISSION_ID}/telemetry")
    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"

@pytest.mark.unit
def test_get_telemetry_data_with_invalid_mission_id_type(client_with_rollback):
    response = client_with_rollback.get("/cosmic-missions/abc/telemetry")
    assert response.status_code == 422
    verify_path_int_parsing_error(response)

@pytest.mark.integration
def test_get_crew_members_by_mission_id(client_with_rollback, mission_with_crew):
    mission_id = mission_with_crew["mission"]["mission_id"]
    expected_crew = mission_with_crew["crew"]

    response = client_with_rollback.get(f"/cosmic-missions/{mission_id}/crew")
    assert response.status_code == 200

    crew = response.json()
    assert isinstance(crew, list)
    assert len(crew) == 2
    assert expected_crew[0] in crew
    assert expected_crew[1] in crew

@pytest.mark.integration
def test_get_crew_members_by_missing_mission_id_failure(client_with_rollback):
    response = client_with_rollback.get(f"/cosmic-missions/{MISSING_MISSION_ID}/crew")
    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"

@pytest.mark.integration
def test_get_crew_members_by_invalid_mission_id_type(client_with_rollback):
    response = client_with_rollback.get("/cosmic-missions/abc/crew")
    assert response.status_code == 422
    verify_path_int_parsing_error(response)

@pytest.mark.integration
def test_get_cosmic_mission_with_crew_size_zero(client_with_rollback, mission_with_crew_size_zero):
    response = client_with_rollback.get(f"/cosmic-missions/{mission_with_crew_size_zero['mission_id']}")
    assert response.status_code == 200
    assert response.json()["crew_size"] == 0

    response = client_with_rollback.get(f"/cosmic-missions/{mission_with_crew_size_zero['mission_id']}/crew")
    assert response.status_code == 200
    assert response.json() == []