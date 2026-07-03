-- ============================================================
-- Phase 1/2 schema: star-schema sales data warehouse
-- ============================================================

DROP TABLE IF EXISTS query_sample CASCADE;
DROP TABLE IF EXISTS experiment_run CASCADE;
DROP TABLE IF EXISTS adaptive_action CASCADE;
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_item CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_store CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- ---------------- Dimensions ----------------

CREATE TABLE dim_date (
    date_key        INTEGER PRIMARY KEY,      -- YYYYMMDD
    full_date       DATE NOT NULL,
    year            SMALLINT NOT NULL,
    quarter         SMALLINT NOT NULL,
    month           SMALLINT NOT NULL,
    day             SMALLINT NOT NULL,
    day_of_week     SMALLINT NOT NULL,
    is_weekend      BOOLEAN NOT NULL
);

CREATE TABLE dim_item (
    item_key        SERIAL PRIMARY KEY,
    item_name       TEXT NOT NULL,
    category        TEXT NOT NULL,
    subcategory     TEXT NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL
);

CREATE TABLE dim_customer (
    customer_key    SERIAL PRIMARY KEY,
    customer_name   TEXT NOT NULL,
    segment         TEXT NOT NULL,
    region          TEXT NOT NULL
);

CREATE TABLE dim_store (
    store_key       SERIAL PRIMARY KEY,
    store_name      TEXT NOT NULL,
    region          TEXT NOT NULL,
    store_type      TEXT NOT NULL
);

-- ---------------- Fact table (partitioned by year) ----------------

CREATE TABLE fact_sales (
    sale_id         BIGSERIAL,
    date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
    item_key        INTEGER NOT NULL REFERENCES dim_item(item_key),
    customer_key    INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    store_key       INTEGER NOT NULL REFERENCES dim_store(store_key),
    quantity        INTEGER NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL,
    net_amount      NUMERIC(12,2) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (sale_id, date_key)
) PARTITION BY RANGE (date_key);

CREATE TABLE fact_sales_2022 PARTITION OF fact_sales
    FOR VALUES FROM (20220101) TO (20230101);
CREATE TABLE fact_sales_2023 PARTITION OF fact_sales
    FOR VALUES FROM (20230101) TO (20240101);
CREATE TABLE fact_sales_2024 PARTITION OF fact_sales
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE fact_sales_2025 PARTITION OF fact_sales
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE fact_sales_default PARTITION OF fact_sales DEFAULT;

-- ---------------- Baseline (static) indexes ----------------

CREATE INDEX idx_fact_2022_item     ON fact_sales_2022 (item_key);
CREATE INDEX idx_fact_2022_customer ON fact_sales_2022 (customer_key);
CREATE INDEX idx_fact_2022_store    ON fact_sales_2022 (store_key);
CREATE INDEX idx_fact_2022_date     ON fact_sales_2022 (date_key);

CREATE INDEX idx_fact_2023_item     ON fact_sales_2023 (item_key);
CREATE INDEX idx_fact_2023_customer ON fact_sales_2023 (customer_key);
CREATE INDEX idx_fact_2023_store    ON fact_sales_2023 (store_key);
CREATE INDEX idx_fact_2023_date     ON fact_sales_2023 (date_key);

CREATE INDEX idx_fact_2024_item     ON fact_sales_2024 (item_key);
CREATE INDEX idx_fact_2024_customer ON fact_sales_2024 (customer_key);
CREATE INDEX idx_fact_2024_store    ON fact_sales_2024 (store_key);
CREATE INDEX idx_fact_2024_date     ON fact_sales_2024 (date_key);

CREATE INDEX idx_fact_2025_item     ON fact_sales_2025 (item_key);
CREATE INDEX idx_fact_2025_customer ON fact_sales_2025 (customer_key);
CREATE INDEX idx_fact_2025_store    ON fact_sales_2025 (store_key);
CREATE INDEX idx_fact_2025_date     ON fact_sales_2025 (date_key);

CREATE INDEX idx_fact_default_item     ON fact_sales_default (item_key);
CREATE INDEX idx_fact_default_customer ON fact_sales_default (customer_key);
CREATE INDEX idx_fact_default_store    ON fact_sales_default (store_key);
CREATE INDEX idx_fact_default_date     ON fact_sales_default (date_key);

-- ---------------- Experiment logging tables ----------------

CREATE TABLE experiment_run (
    run_id          SERIAL PRIMARY KEY,
    label           TEXT NOT NULL,           -- e.g. 'static' or 'adaptive'
    workload        TEXT NOT NULL,           -- product | customer | temporal
    etl_rate        TEXT NOT NULL,           -- zero | low | medium | high
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at        TIMESTAMPTZ,
    notes           TEXT
);

CREATE TABLE query_sample (
    sample_id       BIGSERIAL PRIMARY KEY,
    run_id          INTEGER NOT NULL REFERENCES experiment_run(run_id),
    query_template  TEXT NOT NULL,           -- name of the query in the pool
    latency_ms      DOUBLE PRECISION NOT NULL,
    rows_returned   INTEGER,
    sampled_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE adaptive_action (
    action_id       SERIAL PRIMARY KEY,
    run_id          INTEGER NOT NULL REFERENCES experiment_run(run_id),
    action_type     TEXT NOT NULL,           -- e.g. 'create_index', 'drop_index'
    target          TEXT NOT NULL,           -- table/column affected
    reason          TEXT,
    taken_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_query_sample_run     ON query_sample (run_id);
CREATE INDEX idx_query_sample_tmpl    ON query_sample (query_template);
CREATE INDEX idx_adaptive_action_run  ON adaptive_action (run_id);
