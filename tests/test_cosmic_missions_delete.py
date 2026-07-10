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
