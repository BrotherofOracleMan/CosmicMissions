CREATE TABLE crew_members (
    crew_member_id SERIAL PRIMARY KEY,
    mission_id INTEGER NOT NULL REFERENCES cosmic_missions(mission_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL
);