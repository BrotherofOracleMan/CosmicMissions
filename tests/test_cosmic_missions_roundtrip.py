from decimal import Decimal

import pytest

from payloads.missions import (
    ROUNDTRIP_CREATE,
    ROUNDTRIP_MISSION_ID,
    ROUNDTRIP_PATCH,
    ROUNDTRIP_PUT,
)


@pytest.mark.integration
def test_create_get_delete_roundtrip(client_with_rollback):
    create_response = client_with_rollback.post("/cosmic-missions", json=ROUNDTRIP_CREATE)
    assert create_response.status_code == 200
    assert create_response.json()["mission_id"] == ROUNDTRIP_MISSION_ID
    assert create_response.json()["mission_name"] == "Roundtrip Mission"
    assert Decimal(create_response.json()["budget_billions"]) == Decimal("100.00")

    get_response = client_with_rollback.get(f"/cosmic-missions/{ROUNDTRIP_MISSION_ID}")
    assert get_response.status_code == 200
    assert get_response.json()["destination"] == "Mars"
    assert get_response.json()["telemetry_data"] == {"status": "active"}

    delete_response = client_with_rollback.delete(f"/cosmic-missions/{ROUNDTRIP_MISSION_ID}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Mission deleted successfully"

    get_response = client_with_rollback.get(f"/cosmic-missions/{ROUNDTRIP_MISSION_ID}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Mission not found"


@pytest.mark.integration
def test_full_crud_roundtrip(client_with_rollback):
    create_response = client_with_rollback.post("/cosmic-missions", json=ROUNDTRIP_CREATE)
    assert create_response.status_code == 200

    patch_response = client_with_rollback.patch(f"/cosmic-missions/{ROUNDTRIP_MISSION_ID}", json=ROUNDTRIP_PATCH)
    assert patch_response.status_code == 200
    assert patch_response.json()["mission_name"] == "Roundtrip Mission Patched"
    assert patch_response.json()["is_successful"] is False
    assert patch_response.json()["destination"] == "Mars"

    get_response = client_with_rollback.get(f"/cosmic-missions/{ROUNDTRIP_MISSION_ID}")
    assert get_response.status_code == 200
    assert get_response.json()["mission_name"] == "Roundtrip Mission Patched"
    assert get_response.json()["is_successful"] is False

    put_response = client_with_rollback.put(f"/cosmic-missions/{ROUNDTRIP_MISSION_ID}", json=ROUNDTRIP_PUT)
    assert put_response.status_code == 200
    assert put_response.json()["mission_name"] == "Roundtrip Mission Replaced"
    assert put_response.json()["destination"] == "Jupiter"
    assert Decimal(put_response.json()["budget_billions"]) == Decimal("200.00")
    assert put_response.json()["telemetry_data"] == {"status": "replaced"}

    get_response = client_with_rollback.get(f"/cosmic-missions/{ROUNDTRIP_MISSION_ID}/telemetry")
    assert get_response.status_code == 200
    assert get_response.json() == {"status": "replaced"}

    delete_response = client_with_rollback.delete(f"/cosmic-missions/{ROUNDTRIP_MISSION_ID}")
    assert delete_response.status_code == 200

    get_response = client_with_rollback.get(f"/cosmic-missions/{ROUNDTRIP_MISSION_ID}")
    assert get_response.status_code == 404
