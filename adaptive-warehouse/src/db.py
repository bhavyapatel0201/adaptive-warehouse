"""Thin database helper around psycopg2."""
import contextlib
import psycopg2
import psycopg2.extras

from src.config import DB


def connect(autocommit: bool = False):
    """Open a new connection."""
    conn = psycopg2.connect(
        host=DB["host"], port=DB["port"], dbname=DB["dbname"],
        user=DB["user"], password=DB["password"],
    )
    conn.autocommit = autocommit
    return conn


@contextlib.contextmanager
def cursor(autocommit: bool = False, dict_rows: bool = False):
    """Context-managed cursor that commits/rolls back and closes cleanly."""
    conn = connect(autocommit=autocommit)
    factory = psycopg2.extras.RealDictCursor if dict_rows else None
    cur = conn.cursor(cursor_factory=factory)
    try:
        yield cur
        if not autocommit:
            conn.commit()
    except Exception:
        if not autocommit:
            conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def scalar(sql: str, params=None):
    """Run a query and return the first column of the first row."""
    with cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None
