"""
Product-oriented query pool.

Each entry: (template_name, sql, param_fn)
param_fn(ranges, rng) -> tuple of params for the SQL, using the stdlib
`random.Random` instance passed in so runs can be seeded/reproducible.
"""

QUERIES = [
    (
        "product_point_lookup",
        """
        SELECT sale_id, date_key, customer_key, net_amount
        FROM fact_sales
        WHERE item_key = %s
        ORDER BY date_key DESC
        LIMIT 20;
        """,
        lambda r, rng: (rng.randint(r["item_min"], r["item_max"]),),
    ),
    (
        "product_category_revenue",
        """
        SELECT di.category, sum(fs.net_amount) AS revenue, count(*) AS n
        FROM fact_sales fs
        JOIN dim_item di ON di.item_key = fs.item_key
        WHERE di.category = %s
        GROUP BY di.category;
        """,
        lambda r, rng: (rng.choice(r["categories"]),),
    ),
    (
        "product_top_items",
        """
        SELECT fs.item_key, di.item_name, count(*) AS n_sales,
               sum(fs.net_amount) AS revenue
        FROM fact_sales fs
        JOIN dim_item di ON di.item_key = fs.item_key
        GROUP BY fs.item_key, di.item_name
        ORDER BY revenue DESC
        LIMIT 10;
        """,
        lambda r, rng: (),
    ),
    (
        "product_price_band",
        """
        SELECT count(*) AS n, avg(fs.net_amount) AS avg_amount
        FROM fact_sales fs
        JOIN dim_item di ON di.item_key = fs.item_key
        WHERE di.base_price BETWEEN %s AND %s;
        """,
        lambda r, rng: tuple(sorted([
            round(rng.uniform(5, 500), 2), round(rng.uniform(5, 500), 2)
        ])),
    ),
]
