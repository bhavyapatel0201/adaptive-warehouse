QUERIES = [
    (
        "customer_point_lookup",
        """
        SELECT sale_id, date_key, item_key, net_amount
        FROM fact_sales
        WHERE customer_key = %s
        ORDER BY date_key DESC
        LIMIT 20;
        """,
        lambda r, rng: (rng.randint(r["cust_min"], r["cust_max"]),),
    ),
    (
        "customer_region_revenue",
        """
        SELECT dc.region, sum(fs.net_amount) AS revenue, count(*) AS n
        FROM fact_sales fs
        JOIN dim_customer dc ON dc.customer_key = fs.customer_key
        WHERE dc.region = %s
        GROUP BY dc.region;
        """,
        lambda r, rng: (rng.choice(r["regions"]),),
    ),
    (
        "customer_segment_breakdown",
        """
        SELECT dc.segment, count(DISTINCT fs.customer_key) AS n_customers,
               sum(fs.net_amount) AS revenue
        FROM fact_sales fs
        JOIN dim_customer dc ON dc.customer_key = fs.customer_key
        GROUP BY dc.segment
        ORDER BY revenue DESC;
        """,
        lambda r, rng: (),
    ),
    (
        "customer_top_spenders",
        """
        SELECT fs.customer_key, dc.first_name, dc.last_name, sum(fs.net_amount) AS revenue
        FROM fact_sales fs
        JOIN dim_customer dc ON dc.customer_key = fs.customer_key
        WHERE dc.region = %s
        GROUP BY fs.customer_key, dc.first_name, dc.last_name
        ORDER BY revenue DESC
        LIMIT 10;
        """,
        lambda r, rng: (rng.choice(r["regions"]),),
    ),
]
