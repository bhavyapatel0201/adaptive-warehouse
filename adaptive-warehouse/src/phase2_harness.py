"""
Phase 2 harness: runs a query workload concurrently with the ETL injector
and logs per-query latency into query_sample, tagged to an experiment_run.

Matches this project's actual logging schema:

  experiment_run(run_id, config_id, mode, workload, etl_rate,
                  started_at, finished_at, notes)
  query_sample(sample_id, run_id, query_name, latency_ms, planning_ms,
               used_seqscan, plan_hash, ts)

Each query is run via EXPLAIN (ANALYZE, FORMAT JSON) so latency_ms and
planning_ms come from Postgres itself (server-side execution/planning
time) rather than wall-clock timing on the client, and so we can record
whether the plan used a sequential scan and a stable hash of the plan
shape (useful later for comparing static vs. adaptive indexing).

Usage:
    python -m src.phase2_harness --workload temporal --etl-rate medium \
        --seconds 30 --mode static

Workloads: product | customer | temporal
ETL rates: zero | low | medium | high (see config.ETL_RATES)
"""
import argparse
import hashlib
import json
import random
import threading
import time

import psycopg2

from src.config import DB, ETL_RATES, DEFAULT_RUN_SECONDS
from src.etl_injector import EtlInjector
from src.query_pools import product, customer, temporal
from src.query_pools.common import get_key_ranges

POOLS = {
    "product": product.QUERIES,
    "customer": customer.QUERIES,
    "temporal": temporal.QUERIES,
}


def start_run(conn, mode, workload, etl_rate, config_id=None):
    if config_id is None:
        config_id = f"{workload}_{etl_rate}_{mode}"
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO experiment_run (config_id, mode, workload, etl_rate) "
        "VALUES (%s, %s, %s, %s) RETURNING run_id;",
        (config_id, mode, workload, etl_rate),
    )
    run_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return run_id


def end_run(conn, run_id):
    cur = conn.cursor()
    cur.execute("UPDATE experiment_run SET finished_at = now() WHERE run_id = %s;", (run_id,))
    conn.commit()
    cur.close()


def log_sample(conn, run_id, query_name, latency_ms, planning_ms, used_seqscan, plan_hash):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO query_sample "
        "(run_id, query_name, latency_ms, planning_ms, used_seqscan, plan_hash) "
        "VALUES (%s, %s, %s, %s, %s, %s);",
        (run_id, query_name, latency_ms, planning_ms, used_seqscan, plan_hash),
    )
    conn.commit()
    cur.close()


def _plan_signature(node):
    """Recursively extract (Node Type, Relation Name) pairs from a plan,
    ignoring row counts / costs / timings so the hash is stable across
    runs with the same query shape and only changes when the actual plan
    (index usage, join strategy, etc.) changes."""
    sig = [(node.get("Node Type"), node.get("Relation Name") or node.get("Index Name"))]
    for child in node.get("Plans", []):
        sig.extend(_plan_signature(child))
    return sig


def _contains_seqscan(node):
    if node.get("Node Type") == "Seq Scan":
        return True
    return any(_contains_seqscan(c) for c in node.get("Plans", []))


def run_query_workload(run_id, workload, duration_s, stop_event):
    conn = psycopg2.connect(**DB)
    conn.autocommit = True
    ranges = get_key_ranges(conn)
    rng = random.Random()
    queries = POOLS[workload]

    end_time = time.time() + duration_s
    n_run = 0
    while time.time() < end_time and not stop_event.is_set():
        name, sql, param_fn = rng.choice(queries)
        params = param_fn(ranges, rng)

        cur = conn.cursor()
        try:
            cur.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}", params)
            plan_result = cur.fetchone()[0][0]
            root = plan_result["Plan"]

            latency_ms = plan_result["Execution Time"]
            planning_ms = plan_result["Planning Time"]
            used_seqscan = _contains_seqscan(root)
            plan_hash = hashlib.md5(
                json.dumps(_plan_signature(root)).encode()
            ).hexdigest()[:16]

            log_sample(conn, run_id, name, latency_ms, planning_ms, used_seqscan, plan_hash)
            n_run += 1
        except Exception as e:
            print(f"[harness] query error ({name}): {e}")
        finally:
            cur.close()

    conn.close()
    return n_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workload", choices=list(POOLS.keys()), required=True)
    parser.add_argument("--etl-rate", choices=list(ETL_RATES.keys()), default="zero")
    parser.add_argument("--seconds", type=int, default=DEFAULT_RUN_SECONDS)
    parser.add_argument("--mode", default="static", help="e.g. 'static' or 'adaptive'")
    parser.add_argument("--config-id", default=None, help="optional experiment config label")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    run_id = start_run(conn, args.mode, args.workload, args.etl_rate, args.config_id)
    print(f"Starting run_id={run_id} mode={args.mode} workload={args.workload} "
          f"etl_rate={args.etl_rate} duration={args.seconds}s")

    stop_event = threading.Event()
    injector = EtlInjector(ETL_RATES[args.etl_rate], args.seconds, stop_event)
    injector.start()

    n_run = run_query_workload(run_id, args.workload, args.seconds, stop_event)

    injector.stop()
    injector.join()
    end_run(conn, run_id)

    print(f"Run finished: {n_run} queries logged, "
          f"{injector.rows_inserted} ETL rows inserted ({injector.errors} ETL errors).")
    conn.close()


if __name__ == "__main__":
    main()
