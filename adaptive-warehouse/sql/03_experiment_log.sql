-- =====================================================================
-- 03_experiment_log.sql  |  Metrics + audit tables
-- =====================================================================
-- Everything the experiment harness and adaptive engine produce is
-- written here, so analysis/plots.py can read clean structured data
-- instead of parsing stdout. (This addresses the "log everything to a
-- table" design change.)
--
-- Run:  psql -d salesdw -f sql/03_experiment_log.sql
-- =====================================================================

BEGIN;

-- One row per experiment run (a config x mode combination).
CREATE TABLE IF NOT EXISTS experiment_run (
    run_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    config_id    TEXT        NOT NULL,          -- C1 .. C12
    mode         TEXT        NOT NULL,          -- 'static' | 'adaptive'
    workload     TEXT        NOT NULL,          -- product | customer | temporal
    etl_rate     TEXT        NOT NULL,          -- zero | low | medium | high
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at  TIMESTAMPTZ,
    notes        TEXT
);

-- One row per executed query (fine-grained latency sample).
CREATE TABLE IF NOT EXISTS query_sample (
    sample_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id       BIGINT      NOT NULL REFERENCES experiment_run(run_id),
    query_name   TEXT        NOT NULL,          -- template identifier
    latency_ms   DOUBLE PRECISION NOT NULL,     -- from EXPLAIN ANALYZE
    planning_ms  DOUBLE PRECISION,
    used_seqscan BOOLEAN,                        -- did the plan fall back to a seq scan?
    plan_hash    TEXT,                           -- to detect plan regressions/changes
    ts           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per adaptive action taken (CREATE/DROP INDEX, etc.).
CREATE TABLE IF NOT EXISTS adaptive_action (
    action_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id       BIGINT      NOT NULL REFERENCES experiment_run(run_id),
    action_type  TEXT        NOT NULL,          -- create_index | drop_index | timeout_abort
    target       TEXT        NOT NULL,          -- e.g. fact_sales(item_key)
    reason       TEXT,                           -- why the engine decided this
    duration_ms  DOUBLE PRECISION,              -- how long the DDL took
    succeeded    BOOLEAN     NOT NULL DEFAULT true,
    ts           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_sample_run  ON query_sample (run_id);
CREATE INDEX IF NOT EXISTS ix_action_run  ON adaptive_action (run_id);

COMMIT;

\echo 'Experiment logging tables created.'
