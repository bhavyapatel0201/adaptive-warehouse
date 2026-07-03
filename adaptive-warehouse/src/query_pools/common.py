"""
Shared helpers for query pools.

Query pools never trust config for valid key ranges (that caused the
FK-mismatch bug during ETL testing) -- they always ask the database.
"""


def get_key_ranges(conn):
    cur = conn.cursor()
    cur.execute("SELECT min(item_key), max(item_key) FROM dim_item;")
    item_min, item_max = cur.fetchone()

    cur.execute("SELECT min(customer_key), max(customer_key) FROM dim_customer;")
    cust_min, cust_max = cur.fetchone()

    cur.execute("SELECT min(store_key), max(store_key) FROM dim_store;")
    store_min, store_max = cur.fetchone()

    cur.execute("SELECT min(date_key), max(date_key) FROM dim_date;")
    date_min, date_max = cur.fetchone()

    cur.execute("SELECT DISTINCT category FROM dim_item;")
    categories = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT region FROM dim_customer;")
    regions = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT year FROM dim_date ORDER BY year;")
    years = [r[0] for r in cur.fetchall()]

    cur.close()
    return {
        "item_min": item_min, "item_max": item_max,
        "cust_min": cust_min, "cust_max": cust_max,
        "store_min": store_min, "store_max": store_max,
        "date_min": date_min, "date_max": date_max,
        "categories": categories,
        "regions": regions,
        "years": years,
    }
