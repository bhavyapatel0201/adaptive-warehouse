from dotenv import load_dotenv
load_dotenv()

import os

# --- Database connection ---------------------------
DB = {
    "host": os.getenv("DB_HOST") or os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("DB_PORT") or os.getenv("PGPORT", "5433")),
    "dbname": os.getenv("DB_NAME") or os.getenv("PGDATABASE", "salesdw"),
    "user": os.getenv("DB_USER") or os.getenv("PGUSER", "wh"),
    "password": os.getenv("DB_PASSWORD") or os.getenv("PGPASSWORD", "whpass"),
}

# --- Data generation scale (used by data_gen only) --------
N_CUSTOMERS = int(os.getenv("N_CUSTOMERS", "2000"))
N_ITEMS = int(os.getenv("N_ITEMS", "500"))
N_STORES = int(os.getenv("N_STORES", "50"))

# --- Phase 2: ETL injector rates (rows/sec by label) -------
ETL_RATES = {
    "zero": 0,
    "low": 5,
    "medium": 25,
    "high": 100,
}

# --- Phase 2: default experiment run duration (seconds) ----
DEFAULT_RUN_SECONDS = int(os.getenv("RUN_SECONDS", "30"))
