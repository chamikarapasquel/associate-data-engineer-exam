"""
src/etl/loader.py
PostgreSQL bulk loading engine:
- Loads cleaned records into sales_transactions table
- Loads rejected audit records into rejected_records_log table
- Uses atomic transactions and execute_values for high throughput
"""

import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from src.database import get_connection

def load_clean_data(clean_df: pd.DataFrame, batch_size: int = 1000) -> int:
    """Bulk load cleaned records into PostgreSQL sales_transactions table."""
    if clean_df.empty:
        print("[LOAD] No clean records to load.")
        return 0

    insert_query = """
        INSERT INTO sales_transactions (
            transaction_id, customer_name, category,
            price, quantity, total_amount, rating, country, created_date
        ) VALUES %s
        ON CONFLICT (transaction_id) DO UPDATE SET
            customer_name = EXCLUDED.customer_name,
            category = EXCLUDED.category,
            price = EXCLUDED.price,
            quantity = EXCLUDED.quantity,
            total_amount = EXCLUDED.total_amount,
            rating = EXCLUDED.rating,
            country = EXCLUDED.country,
            created_date = EXCLUDED.created_date,
            ingested_at = CURRENT_TIMESTAMP;
    """

    records = [
        (
            row["transaction_id"],
            row["customer_name"],
            row["category"],
            row["price"],
            row["quantity"],
            row["total_amount"],
            row["rating"],
            row["country"],
            row["created_date"]
        )
        for _, row in clean_df.iterrows()
    ]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_values(cur, insert_query, records, page_size=batch_size)
        conn.commit()
        print(f"[LOAD] Successfully loaded {len(records):,} records into 'sales_transactions' table.")
        return len(records)
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Bulk load failed, transaction rolled back: {e}")
        raise e
    finally:
        conn.close()


def load_rejected_data(rejected_df: pd.DataFrame, batch_size: int = 1000) -> int:
    """Store quarantined audit logs into PostgreSQL rejected_records_log table."""
    if rejected_df.empty:
        return 0

    insert_query = """
        INSERT INTO rejected_records_log (
            raw_transaction_id, rejection_reason, customer_name, category,
            price, quantity, rating, country, created_date
        ) VALUES %s;
    """

    records = [
        (
            str(row.get("transaction_id", "")),
            str(row.get("rejection_reason", "UNKNOWN_ERROR")),
            str(row.get("customer_name", "")),
            str(row.get("category", "")),
            str(row.get("price", "")),
            str(row.get("quantity", "")),
            str(row.get("rating", "")),
            str(row.get("country", "")),
            str(row.get("created_date", ""))
        )
        for _, row in rejected_df.iterrows()
    ]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_values(cur, insert_query, records, page_size=batch_size)
        conn.commit()
        print(f"[LOAD] Successfully logged {len(records):,} quarantine records into 'rejected_records_log'.")
        return len(records)
    except Exception as e:
        conn.rollback()
        print(f"[WARN] Failed to load rejected records to DB: {e}")
        return 0
    finally:
        conn.close()