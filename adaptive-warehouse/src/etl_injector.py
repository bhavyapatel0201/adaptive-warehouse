"""
ETL injector: simulates ongoing write load against fact_sales while a
query workload runs concurrently.

Runs as a background thread inside the harness (see harness.py), or
standalone via:

    python -m src.etl_injector --rate medium --seconds 30
"""
import argparse
import random
import threading
import time

import psycopg2

from src.config import DB, ETL_RATES
from src.query_pools.common import get_key_ranges


class EtlInjector(threading.Thread):
    """Inserts rows into fact_sales at ~`rows_per_sec` for `duration_s` seconds.

    Valid item/customer/store key ranges are pulled live from the database
    at start time rather than trusted from config, since config can drift
    out of sync with what was actually generated.
    """

    def __init__(self, rows_per_sec, duration_s, stop_event=None):
        super().__init__(daemon=True)
        self.rows_per_sec = rows_per_sec
        self.duration_s = duration_s
        self.stop_event = stop_event or threading.Event()
        self.rows_inserted = 0
        self.errors = 0

    def run(self):
        if self.rows_per_sec <= 0:
            return

        conn = psycopg2.connect(**DB)
        conn.autocommit = True
        cur = conn.cursor()

        ranges = get_key_ranges(conn)
        rng = random.Random()

        # newest date partition, so ETL writes land in the "hot" partition.
        # Pull the actual valid date_keys for that year -- YYYYMMDD is NOT
        # a contiguous integer range (e.g. 20250851 isn't a real date), so
        # this must come from dim_date rather than randint() over the range.
        year = max(ranges["years"])
        hot_year_cur = conn.cursor()
        hot_year_cur.execute("SELECT date_key FROM dim_date WHERE year = %s;", (year,))
        hot_year_date_keys = [r[0] for r in hot_year_cur.fetchall()]
        hot_year_cur.close()

        interval = 1.0 / self.rows_per_sec
        end_time = time.time() + self.duration_s

        insert_sql = """
            INSERT INTO fact_sales
                (date_key, item_key, customer_key, store_key,
                 quantity, unit_price, net_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        while time.time() < end_time and not self.stop_event.is_set():
            date_key = rng.choice(hot_year_date_keys)
            item_key = rng.randint(ranges["item_min"], ranges["item_max"])
            customer_key = rng.randint(ranges["cust_min"], ranges["cust_max"])
            store_key = rng.randint(ranges["store_min"], ranges["store_max"])
            quantity = rng.randint(1, 10)
            unit_price = round(rng.uniform(5, 500), 2)
            net_amount = round(quantity * unit_price, 2)

            try:
                cur.execute(insert_sql, (date_key, item_key, customer_key,
                                          store_key, quantity, unit_price, net_amount))
                self.rows_inserted += 1
            except Exception as e:
                self.errors += 1
                print(f"[etl_injector] insert error: {e}")

            time.sleep(interval)

        cur.close()
        conn.close()

    def stop(self):
        self.stop_event.set()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", choices=list(ETL_RATES.keys()), default="low")
    parser.add_argument("--seconds", type=int, default=30)
    args = parser.parse_args()

    rows_per_sec = ETL_RATES[args.rate]
    print(f"Starting ETL injector: rate={args.rate} ({rows_per_sec} rows/sec), "
          f"duration={args.seconds}s")

    injector = EtlInjector(rows_per_sec, args.seconds)
    injector.start()
    injector.join()

    print(f"ETL injector finished. Inserted {injector.rows_inserted} rows, "
          f"{injector.errors} errors.")


if __name__ == "__main__":
    main()
