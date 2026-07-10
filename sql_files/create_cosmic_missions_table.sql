CREATE TABLE cosmic_missions (
    mission_id       INTEGER PRIMARY KEY,
    mission_name     VARCHAR(255) NOT NULL,
    destination      VARCHAR(255) NOT NULL,
    launch_date      DATE NOT NULL,
    crew_size        INTEGER NOT NULL DEFAULT 0,
    budget_billions  NUMERIC(10, 2) NOT NULL,
    is_successful    BOOLEAN NOT NULL,
    telemetry_data   JSONB
);
