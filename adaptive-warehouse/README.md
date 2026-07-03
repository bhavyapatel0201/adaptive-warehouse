# Phase 2 — Workload Generator + ETL Injector

## Setup

```powershell
pip install -r requirements.txt
copy .env.example .env   # edit DB_* values to match your Docker Postgres
python -m src.data_gen.generate --rows 500000   # if Phase 1 data isn't loaded yet
```

## Running an experiment

```powershell
python -m src.harness --workload temporal --etl-rate medium --seconds 30 --label static
```

- `--workload`: product | customer | temporal
- `--etl-rate`: zero | low | medium | high  (rows/sec, see src/config.py:ETL_RATES)
- `--label`: free-text tag for the run (e.g. static vs adaptive later in Phase 3)
- `--seconds`: run duration

Each run logs one row to `experiment_run` and one row per query executed to
`query_sample` (latency_ms, rows_returned, query_template). The ETL injector
runs concurrently in a background thread and writes directly into the hot
(most recent year's) partition.

## Standalone ETL injector

```powershell
python -m src.etl_injector --rate high --seconds 30
```

## Files

- `sql/schema.sql` — star schema (4 dims + partitioned fact_sales + log tables)
- `src/config.py` — DB connection + rate/scale settings, loaded from `.env`
- `src/data_gen/generate.py` — Phase 1 synthetic data generator (Zipf item skew, recency date skew)
- `src/query_pools/{product,customer,temporal}.py` — parameterized query templates
- `src/query_pools/common.py` — pulls live key ranges from the DB (never trusts config)
- `src/etl_injector.py` — background thread that inserts rows at a configurable rate
- `src/harness.py` — runs a query pool + ETL concurrently, logs latency to `query_sample`

## Notes / gotchas found while building this

- The ETL injector must look up valid item/customer/store key ranges from the
  DB at runtime, not from `config.py` — config can drift out of sync with
  what was actually generated, which causes FK violations.
- `date_key` is `YYYYMMDD` as an integer, but it is **not** a contiguous
  range — `random.randint(20250101, 20251231)` will generate invalid dates
  like `20250851`. Always sample real date_keys from `dim_date` instead.
