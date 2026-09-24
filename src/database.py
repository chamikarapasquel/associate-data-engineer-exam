"""
src/database.py
PostgreSQL connection and schema execution helper.
"""

import psycopg2
from src.config import db_config

def get_connection():
    """Establish and return a new connection to PostgreSQL."""
    return psycopg2.connect(
        host=db_config.host,
        port=db_config.port,
        dbname=db_config.name,
        user=db_config.user,
        password=db_config.password
    )

def test_connection():
    """Test PostgreSQL connectivity and print version."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            ver = cur.fetchone()[0]
            print(f"[SUCCESS] Connected to PostgreSQL: {ver}")
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to PostgreSQL: {e}")
        return False

def apply_schema(schema_file_path: str = "sql/01_schema.sql"):
    """Read and execute a SQL schema file."""
    conn = get_connection()
    try:
        with open(schema_file_path, "r", encoding="utf-8") as f:
            sql = f.read()
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print(f"[SUCCESS] Applied schema from: {schema_file_path}")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to apply schema: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    if test_connection():
        apply_schema()