# --- Mission IDs ---

MISSING_MISSION_ID = 999999
TEST_MISSION_ID = 99999
ROUNDTRIP_MISSION_ID = 99997

# --- Response shape ---

EXPECTED_MISSION_KEYS = {
    "mission_id",
    "mission_name",
    "destination",
    "launch_date",
    "crew_size",
    "budget_billions",
    "is_successful",
    "telemetry_data",
}

# --- Seed payloads ---

APOLLO_11 = {
    "mission_id": 1,
    "mission_name": "Apollo 11",
    "destination": "Moon",
    "launch_date": "1969-07-16",
    "crew_size": 3,
    "budget_billions": 25.40,
    "is_successful": True,
    "telemetry_data": {"landing_site": "Tranquility Base", "duration_days": 8},
}

DUPLICATE_TEST_MISSION = {
    "mission_id": 1,
    "mission_name": "Test Mission",
    "destination": "Test Destination",
    "launch_date": "2026-01-01",
    "crew_size": 1,
    "budget_billions": 20,
    "is_successful": True,
    "telemetry_data": {"test": "test"},
}

SUCCESSFUL_MISSION = {
    "mission_id": 1,
    "mission_name": "Successful Mission 1",
    "destination": "Mars",
    "launch_date": "1969-07-16",
    "crew_size": 3,
    "budget_billions": 25.40,
    "is_successful": True,
    "telemetry_data": {"landing_site": "Tranquility Base", "duration_days": 8},
}

UNSUCCESSFUL_MISSION = {
    "mission_id": 2,
    "mission_name": "Unsuccessful Mission 1",
    "destination": "Mars",
    "launch_date": "1969-07-16",
    "crew_size": 3,
    "budget_billions": 25.40,
    "is_successful": False,
    "telemetry_data": None,
}

NULL_TELEMETRY_MISSION = {
    "mission_id": TEST_MISSION_ID,
    "mission_name": "Null Telemetry Mission",
    "destination": "Mars",
    "telemetry_data": None,
}

MINIMAL_MISSION = {
    "mission_id": TEST_MISSION_ID,
    "mission_name": "Test Mission 99999",
    "destination": "Test Destination 99999",
    "launch_date": "2026-06-23",
}

# --- Crew create bodies (POST /cosmic-missions/{id}/crew) ---

CREW_MEMBER_1 = {
    "name": "John Doe",
    "role": "Astronaut",
}

CREW_MEMBER_2 = {
    "name": "Jane Doe",
    "role": "Engineer",
}

# --- CRUD payloads (body fields only unless noted) ---

BASE_MISSION = {
    "mission_name": "Test Mission 99999",
    "destination": "Test Destination 99999",
    "launch_date": "2026-06-23",
    "crew_size": 1,
    "budget_billions": 99999,
    "is_successful": True,
    "telemetry_data": {"test": "test"},
}

FULL_PUT_UPDATE = {
    "mission_name": "Updated Test Mission 99999",
    "destination": "Updated Test Destination 99999",
    "launch_date": "2026-06-24",
    "crew_size": 2,
    "budget_billions": 8000,
    "is_successful": False,
    "telemetry_data": {"test": "updated test"},
}

ROUNDTRIP_CREATE = {
    "mission_id": ROUNDTRIP_MISSION_ID,
    "mission_name": "Roundtrip Mission",
    "destination": "Mars",
    "launch_date": "2026-06-23",
    "crew_size": 1,
    "budget_billions": 100,
    "is_successful": True,
    "telemetry_data": {"status": "active"},
}

ROUNDTRIP_PATCH = {
    "mission_name": "Roundtrip Mission Patched",
    "is_successful": False,
}

ROUNDTRIP_PUT = {
    "mission_name": "Roundtrip Mission Replaced",
    "destination": "Jupiter",
    "launch_date": "2026-07-01",
    "crew_size": 3,
    "budget_billions": 200,
    "is_successful": True,
    "telemetry_data": {"status": "replaced"},
}
