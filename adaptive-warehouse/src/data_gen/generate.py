"""
Loads dimension tables and generates synthetic fact_sales rows with
Zipf skew on items and recency skew on dates (more rows in later years).

Usage:
    python -m src.data_gen.generate [--rows 500000]
"""
import argparse
import random
from datetime import date, timedelta

import psycopg2
import psycopg2.extras

from src.config import DB, N_CUSTOMERS, N_ITEMS, N_STORES

CATEGORIES = {
    "Electronics": ["Phones", "Laptops", "Audio", "Accessories"],
    "Home": ["Kitchen", "Furniture", "Decor"],
    "Apparel": ["Mens", "Womens", "Kids"],
    "Grocery": ["Produce", "Snacks", "Beverages"],
    "Sports": ["Fitness", "Outdoor", "Team Sports"],
}
REGIONS = ["North", "South", "East", "West", "Central"]
SEGMENTS = ["Consumer", "SMB", "Enterprise"]
STORE_TYPES = ["Flagship", "Mall", "Outlet", "Online"]

YEARS = [2022, 2023, 2024, 2025]
# recency skew: later years get more rows
YEAR_WEIGHTS = [0.08, 0.20, 0.32, 0.40]


def connect():
    return psycopg2.connect(**DB)


def load_dimensions(conn):
    cur = conn.cursor()

    print(f"Loading dim_date ({YEARS[0]}-01-01 .. {YEARS[-1]}-12-31)...")
    d = date(YEARS[0], 1, 1)
    end = date(YEARS[-1], 12, 31)
    rows = []
    while d <= end:
        key = int(d.strftime("%Y%m%d"))
        rows.append((
            key, d, d.year, (d.month - 1) // 3 + 1, d.month, d.day,
            d.isoweekday(), d.isoweekday() >= 6,
        ))
        d += timedelta(days=1)
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO dim_date (date_key, full_date, year, quarter, month, day, day_of_week, is_weekend) VALUES %s",
        rows,
    )

    print(f"Loading dim_item ({N_ITEMS} rows)...")
    rows = []
    for i in range(N_ITEMS):
        cat = random.choice(list(CATEGORIES.keys()))
        subcat = random.choice(CATEGORIES[cat])
        price = round(random.uniform(5, 500), 2)
        rows.append((f"Item {i+1}", cat, subcat, price))
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO dim_item (item_name, category, subcategory, unit_price) VALUES %s",
        rows,
    )

    print(f"Loading dim_customer ({N_CUSTOMERS} rows)...")
    rows = [
        (f"Customer {i+1}", random.choice(SEGMENTS), random.choice(REGIONS))
        for i in range(N_CUSTOMERS)
    ]
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO dim_customer (customer_name, segment, region) VALUES %s",
        rows,
    )

    print(f"Loading dim_store ({N_STORES} rows)...")
    rows = [
        (f"Store {i+1}", random.choice(REGIONS), random.choice(STORE_TYPES))
        for i in range(N_STORES)
    ]
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO dim_store (store_name, region, store_type) VALUES %s",
        rows,
    )

    conn.commit()
    cur.close()


def zipf_item_keys(n_items, size, s=1.3):
    """Sample item_key ids with Zipf skew (item 1 sold far more often)."""
    ranks = list(range(1, n_items + 1))
    weights = [1.0 / (r ** s) for r in ranks]
    return random.choices(ranks, weights=weights, k=size)


def date_keys_for_year(year):
    d = date(year, 1, 1)
    end = date(year, 12, 31)
    keys = []
    while d <= end:
        keys.append(int(d.strftime("%Y%m%d")))
        d += timedelta(days=1)
    return keys


def generate_facts(conn, total_rows):
    cur = conn.cursor()

    per_year = [int(total_rows * w) for w in YEAR_WEIGHTS]
    # fix rounding drift on the last year
    per_year[-1] += total_rows - sum(per_year)

    for year, n in zip(YEARS, per_year):
        print(f"Generating {n} rows for {year}...")
        year_dates = date_keys_for_year(year)
        item_keys = zipf_item_keys(N_ITEMS, n)

        batch = []
        batch_size = 20000
        for i in range(n):
            date_key = random.choice(year_dates)
            item_key = item_keys[i]
            customer_key = random.randint(1, N_CUSTOMERS)
            store_key = random.randint(1, N_STORES)
            quantity = random.randint(1, 10)
            unit_price = round(random.uniform(5, 500), 2)
            net_amount = round(quantity * unit_price, 2)
            batch.append((date_key, item_key, customer_key, store_key,
                           quantity, unit_price, net_amount))
            if len(batch) >= batch_size:
                psycopg2.extras.execute_values(
                    cur,
                    "INSERT INTO fact_sales (date_key, item_key, customer_key, "
                    "store_key, quantity, unit_price, net_amount) VALUES %s",
                    batch,
                )
                conn.commit()
                batch = []
        if batch:
            psycopg2.extras.execute_values(
                cur,
                "INSERT INTO fact_sales (date_key, item_key, customer_key, "
                "store_key, quantity, unit_price, net_amount) VALUES %s",
                batch,
            )
            conn.commit()

    cur.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=500_000)
    args = parser.parse_args()

    conn = connect()
    try:
        load_dimensions(conn)
        generate_facts(conn, args.rows)
        print("Running ANALYZE...")
        cur = conn.cursor()
        cur.execute("ANALYZE;")
        conn.commit()
        cur.close()
        print(f"Data generation finished. {args.rows} fact rows loaded.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
