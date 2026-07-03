QUERIES = [
    (
        "temporal_single_year_revenue",
        """
        SELECT sum(net_amount) AS revenue, count(*) AS n
        FROM fact_sales
        WHERE date_key BETWEEN %s AND %s;
        """,
        lambda r, rng: _single_year_bounds(r, rng),
    ),
    (
        "temporal_monthly_trend",
        """
        SELECT dd.year, dd.month, sum(fs.net_amount) AS revenue
        FROM fact_sales fs
        JOIN dim_date dd ON dd.date_key = fs.date_key
        WHERE dd.year = %s
        GROUP BY dd.year, dd.month
        ORDER BY dd.month;
        """,
        lambda r, rng: (rng.choice(r["years"]),),
    ),
    (
        "temporal_recent_window",
        """
        SELECT count(*) AS n, sum(net_amount) AS revenue
        FROM fact_sales
        WHERE date_key BETWEEN %s AND %s;
        """,
        lambda r, rng: _recent_window(r, rng),
    ),
    (
        "temporal_weekend_vs_weekday",
        """
        SELECT dd.is_weekend, count(*) AS n, avg(fs.net_amount) AS avg_amount
        FROM fact_sales fs
        JOIN dim_date dd ON dd.date_key = fs.date_key
        WHERE dd.year = %s
        GROUP BY dd.is_weekend;
        """,
        lambda r, rng: (rng.choice(r["years"]),),
    ),
]


def _single_year_bounds(r, rng):
    year = rng.choice(r["years"])
    return (int(f"{year}0101"), int(f"{year}1231"))


def _recent_window(r, rng):
    # a ~30 day window within the most recent year, for pruning tests
    year = max(r["years"])
    start_day = rng.randint(1, 335)
    start = int(f"{year}{1:02d}01") + start_day  # rough offset, not calendar-exact
    # clamp into a safe simple window instead of doing calendar math here
    start_key = int(f"{year}0601")
    end_key = int(f"{year}0630")
    return (start_key, end_key)
