-- =====================================================================
-- 01_schema.sql  |  Global Sales Data Warehouse - Star Schema
-- =====================================================================
-- Central FactSales table surrounded by four dimensions:
--   DimItem, DimCustomer, DimStore, DimDate
--
-- FactSales is RANGE-partitioned by year (via date_key) so the project
-- can study partition pruning and adaptive partition behaviour, exactly
-- as described in the proposal's System Architecture section.
--
-- Run:  psql -d salesdw -f sql/01_schema.sql
-- =====================================================================

BEGIN;

DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_item CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_store CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- ---------------------------------------------------------------------
-- Dimension: Item  (drives "product-centric" query phase)
-- ---------------------------------------------------------------------
CREATE TABLE dim_item (
    item_key     INTEGER PRIMARY KEY,
    item_name    TEXT        NOT NULL,
    category     TEXT        NOT NULL,
    subcategory  TEXT        NOT NULL,
    brand        TEXT        NOT NULL,
    base_price   NUMERIC(10,2) NOT NULL
);

-- ---------------------------------------------------------------------
-- Dimension: Customer  (drives "customer-centric" query phase)
-- ---------------------------------------------------------------------
CREATE TABLE dim_customer (
    customer_key       INTEGER PRIMARY KEY,
    first_name         TEXT NOT NULL,
    last_name          TEXT NOT NULL,
    email              TEXT NOT NULL,
    segment            TEXT NOT NULL,   -- consumer | business | premium
    country            TEXT NOT NULL,
    region             TEXT NOT NULL,
    city               TEXT NOT NULL,
    registration_date  DATE NOT NULL
);

-- ---------------------------------------------------------------------
-- Dimension: Store
-- ---------------------------------------------------------------------
CREATE TABLE dim_store (
    store_key   INTEGER PRIMARY KEY,
    store_name  TEXT NOT NULL,
    store_type  TEXT NOT NULL,          -- flagship | outlet | online | popup
    country     TEXT NOT NULL,
    region      TEXT NOT NULL,
    city        TEXT NOT NULL
);

-- ---------------------------------------------------------------------
-- Dimension: Date  (drives "temporal-centric" query phase)
-- date_key is an integer surrogate in YYYYMMDD form.
-- ---------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key     INTEGER PRIMARY KEY,   -- e.g. 20240315
    full_date    DATE    NOT NULL,
    day          SMALLINT NOT NULL,
    month        SMALLINT NOT NULL,
    quarter      SMALLINT NOT NULL,
    year         SMALLINT NOT NULL,
    day_of_week  SMALLINT NOT NULL,     -- 0=Mon .. 6=Sun
    is_weekend   BOOLEAN  NOT NULL,
    season       TEXT     NOT NULL      -- Winter | Spring | Summer | Fall
);

-- ---------------------------------------------------------------------
-- Fact: Sales  (RANGE partitioned by year via date_key)
-- created_at lets the ETL injector mark newly ingested rows so the
-- adaptive engine / analysis can reason about ingestion recency.
-- ---------------------------------------------------------------------
CREATE TABLE fact_sales (
    sale_id       BIGINT       GENERATED ALWAYS AS IDENTITY,
    item_key      INTEGER      NOT NULL REFERENCES dim_item(item_key),
    customer_key  INTEGER      NOT NULL REFERENCES dim_customer(customer_key),
    store_key     INTEGER      NOT NULL REFERENCES dim_store(store_key),
    date_key      INTEGER      NOT NULL REFERENCES dim_date(date_key),
    quantity      INTEGER      NOT NULL,
    unit_price    NUMERIC(10,2) NOT NULL,
    discount      NUMERIC(10,2) NOT NULL DEFAULT 0,
    net_amount    NUMERIC(12,2) NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    PRIMARY KEY (sale_id, date_key)
) PARTITION BY RANGE (date_key);

-- Yearly partitions. Add more here (or let a helper create them) if you
-- extend the generated date range.
CREATE TABLE fact_sales_2022 PARTITION OF fact_sales
    FOR VALUES FROM (20220101) TO (20230101);
CREATE TABLE fact_sales_2023 PARTITION OF fact_sales
    FOR VALUES FROM (20230101) TO (20240101);
CREATE TABLE fact_sales_2024 PARTITION OF fact_sales
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE fact_sales_2025 PARTITION OF fact_sales
    FOR VALUES FROM (20250101) TO (20260101);

-- Catch-all so ETL inserts never fail on an out-of-range date_key.
CREATE TABLE fact_sales_default PARTITION OF fact_sales DEFAULT;

COMMIT;

-- Quick sanity echo
\echo 'Schema created. Tables:'
\dt
