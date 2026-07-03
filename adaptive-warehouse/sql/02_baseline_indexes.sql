-- =====================================================================
-- 02_baseline_indexes.sql  |  STATIC baseline physical design
-- =====================================================================
-- This is the CONTROL GROUP. These indexes are created once and never
-- touched during static-mode experiments. The adaptive engine, by
-- contrast, starts from THIS SAME baseline and then adds/drops indexes
-- at runtime based on observed workload.
--
-- Deliberately conservative: primary keys already exist, so here we add
-- only the foreign-key join columns a DBA would obviously index up front.
-- We intentionally do NOT pre-index every filter column, so the adaptive
-- engine has room to demonstrate value.
--
-- Run:  psql -d salesdw -f sql/02_baseline_indexes.sql
-- =====================================================================

BEGIN;

-- Foreign-key columns on the fact table (standard star-join support).
CREATE INDEX IF NOT EXISTS ix_fact_item     ON fact_sales (item_key);
CREATE INDEX IF NOT EXISTS ix_fact_customer ON fact_sales (customer_key);
CREATE INDEX IF NOT EXISTS ix_fact_store    ON fact_sales (store_key);
-- date_key is the partition key; per-partition local index still helps range scans.
CREATE INDEX IF NOT EXISTS ix_fact_date     ON fact_sales (date_key);

-- A couple of obvious dimension lookups.
CREATE INDEX IF NOT EXISTS ix_item_category   ON dim_item (category);
CREATE INDEX IF NOT EXISTS ix_customer_segment ON dim_customer (segment);

COMMIT;

\echo 'Baseline (static) indexes created.'
