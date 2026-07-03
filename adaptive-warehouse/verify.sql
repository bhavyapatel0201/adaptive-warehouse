-- Phase 1 verification checks

\echo '--- Check 1: Tables ---'
\dt

\echo '--- Check 2: Partition row counts ---'
SELECT tableoid::regclass AS partition, count(*)
FROM fact_sales GROUP BY 1 ORDER BY 1;

\echo '--- Check 3: Zipf skew on items ---'
SELECT item_key, count(*) AS sales FROM fact_sales
GROUP BY item_key ORDER BY sales DESC LIMIT 5;

\echo '--- Check 4: Partition pruning ---'
EXPLAIN (COSTS OFF)
SELECT sum(net_amount) FROM fact_sales
WHERE date_key BETWEEN 20240101 AND 20241231;

\echo '--- Check 5: Baseline indexes ---'
\di

\echo '--- Check 6: Log tables ---'
\dt experiment_run
\dt query_sample
\dt adaptive_action
