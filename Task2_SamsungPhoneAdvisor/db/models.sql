-- db/models.sql

CREATE TABLE IF NOT EXISTS phones (
    id SERIAL PRIMARY KEY,
    name TEXT,
    model_normalized TEXT,
    year INT,
    release_date TEXT,
    status TEXT,
    price NUMERIC,
    network JSONB,
    launch JSONB,
    body JSONB,
    display JSONB,
    platform JSONB,
    memory JSONB,
    camera JSONB,
    comms JSONB,
    features JSONB,
    battery JSONB,
    misc JSONB,
    full_specs JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_phones_name ON phones (name);
CREATE INDEX IF NOT EXISTS idx_phones_model_norm ON phones (model_normalized);
CREATE INDEX IF NOT EXISTS idx_phones_year ON phones (year);
