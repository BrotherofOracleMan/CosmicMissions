from decimal import Decimal


def verify_mission_fields(mission: dict, expected: dict) -> None:
    assert mission["mission_id"] == expected["mission_id"]
    assert mission["mission_name"] == expected["mission_name"]
    assert mission["destination"] == expected["destination"]
    assert mission["launch_date"] == expected["launch_date"]
    assert mission["crew_size"] == expected["crew_size"]
    assert Decimal(mission["budget_billions"]) == Decimal(str(expected["budget_billions"]))
    assert mission["is_successful"] is expected["is_successful"]
    if "telemetry_data" in expected:
        assert mission["telemetry_data"] == expected["telemetry_data"]


def verify_path_int_parsing_error(response) -> None:
    detail = response.json()["detail"][0]
    assert detail["type"] == "int_parsing"
    assert detail["loc"] == ["path", "mission_id"]
    assert detail["msg"] == "Input should be a valid integer, unable to parse string as an integer"
