# Convenience commands. Run `make help` to see them.
PSQL = psql -h $(or $(PGHOST),localhost) -U $(or $(PGUSER),wh) -d $(or $(PGDATABASE),salesdw)
export PGPASSWORD ?= wh

.PHONY: help db-up db-down schema baseline logtables load setup reset psql

help:
	@echo "make db-up      - start Postgres 16 via Docker"
	@echo "make db-down    - stop Postgres"
	@echo "make schema     - create star schema"
	@echo "make baseline   - create static baseline indexes"
	@echo "make logtables  - create experiment log tables"
	@echo "make load       - generate + load synthetic data"
	@echo "make setup      - schema + baseline + logtables + load (full bootstrap)"
	@echo "make reset      - drop and recreate everything"
	@echo "make psql       - open a psql shell"

db-up:
	docker compose up -d
	@echo "Waiting for Postgres to be healthy..."
	@until docker exec salesdw_pg pg_isready -U wh -d salesdw >/dev/null 2>&1; do sleep 1; done
	@echo "Postgres is ready. Enabling pg_stat_statements extension..."
	$(PSQL) -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

db-down:
	docker compose down

schema:
	$(PSQL) -f sql/01_schema.sql

baseline:
	$(PSQL) -f sql/02_baseline_indexes.sql

logtables:
	$(PSQL) -f sql/03_experiment_log.sql

load:
	python -m src.data_gen.generate

setup: schema baseline logtables load
	@echo "Full setup complete."

reset: schema baseline logtables load
	@echo "Reset complete."

psql:
	$(PSQL)
