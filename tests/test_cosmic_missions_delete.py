import pytest
from assertions import verify_path_int_parsing_error
from payloads.missions import MISSING_MISSION_ID

@pytest.mark.integration
def test_delete_cosmic_mission_failure(client_with_rollback):
    response = client_with_rollback.delete(f"/cosmic-missions/{MISSING_MISSION_ID}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"

@pytest.mark.integration
def test_delete_cosmic_mission_success(client_with_rollback, created_minimal_mission):
    response = client_with_rollback.delete(f"/cosmic-missions/{created_minimal_mission}")
    assert response.status_code == 200
    assert response.json()["message"] == "Mission deleted successfully"

    get_response = client_with_rollback.get(f"/cosmic-missions/{created_minimal_mission}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Mission not found"

@pytest.mark.unit
def test_delete_cosmic_mission_with_invalid_path_parameter(client_with_rollback):
    response = client_with_rollback.delete("/cosmic-missions/abc")
    assert response.status_code == 422
    verify_path_int_parsing_error(response)

@pytest.mark.integration
def test_delete_crew_member_happy_path(client_with_rollback, crew_member_1):
    response = client_with_rollback.delete(f"/cosmic-missions/{crew_member_1['mission_id']}/crew/{crew_member_1['crew_member_id']}")
    assert response.status_code == 200
    assert response.json()["message"] == "Crew member deleted successfully"

    get_response = client_with_rollback.get(f"/cosmic-missions/{crew_member_1['mission_id']}/crew")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 0

@pytest.mark.integration
def test_delete_mission_with_crew_members(client_with_rollback, crew_member_1):
    response = client_with_rollback.delete(f"/cosmic-missions/{crew_member_1['mission_id']}")
    assert response.status_code == 200
    assert response.json()["message"] == "Mission deleted successfully"

    get_response = client_with_rollback.get(f"/cosmic-missions/{crew_member_1['mission_id']}/crew")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Mission not found"

@pytest.mark.integration
def test_missing_crew_member_on_existing_mission(client_with_rollback, crew_member_1):
    response = client_with_rollback.delete(f"/cosmic-missions/{crew_member_1['mission_id']}/crew/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Crew member not found"

@pytest.mark.integration
def test_delete_crew_member_with_missing_mission_id_failure(client_with_rollback):
    response = client_with_rollback.delete(f"/cosmic-missions/{MISSING_MISSION_ID}/crew/1")
    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"

@pytest.mark.integration
def test_delete_crew_member_with_wrong_mission_crew_pair(client_with_rollback, crew_member_1, created_minimal_mission):
    response = client_with_rollback.delete(f"/cosmic-missions/{created_minimal_mission}/crew/{crew_member_1['crew_member_id']}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Crew member not found"

    get_response = client_with_rollback.get(f"/cosmic-missions/{crew_member_1['mission_id']}/crew")
    assert get_response.status_code == 200
    assert get_response.json() == [crew_member_1]
    assert len(get_response.json()) == 1

@pytest.mark.unit
def test_invalid_crew_member_id_type(client_with_rollback, created_minimal_mission):
    response = client_with_rollback.delete(f"/cosmic-missions/{created_minimal_mission}/crew/abc")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "int_parsing"
    assert response.json()["detail"][0]["msg"] == "Input should be a valid integer, unable to parse string as an integer"
    assert response.json()["detail"][0]["loc"] == ['path', 'crew_member_id']

