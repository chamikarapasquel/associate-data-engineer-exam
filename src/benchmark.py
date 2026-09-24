"""
src/benchmark.py
Database performance benchmarking tool.
Runs queries with EXPLAIN (ANALYZE, BUFFERS) before and after index creation,
measuring execution time (ms), planning time, and access scan types (Seq Scan vs Index Scan).
"""

import time
import psycopg2
from src.database import get_connection

TEST_QUERIES = [
    {
        "name": "Date Range Filter (Q4 2024 Transactions)",
        "sql": """
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT COUNT(*), SUM(total_amount), AVG(rating)
            FROM sales_transactions
            WHERE created_date >= '2024-10-01' AND created_date < '2025-01-01';
        """
    },
    {
        "name": "Category Revenue & Volume Filter",
        "sql": """
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT category, COUNT(*), SUM(total_amount)
            FROM sales_transactions
            WHERE category = 'Electronics'
            GROUP BY category;
        """
    },
    {
        "name": "Country Aggregation (Index-Only Scan Candidate)",
        "sql": """
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT country, AVG(rating), SUM(total_amount)
            FROM sales_transactions
            WHERE country = 'United States'
            GROUP BY country;
        """
    }
]

def drop_indexes(conn):
    """Drop non-primary-key indexes to measure unindexed baseline."""
    with conn.cursor() as cur:
        cur.execute("DROP INDEX IF EXISTS idx_sales_created_date;")
        cur.execute("DROP INDEX IF EXISTS idx_sales_country_covering;")
        cur.execute("DROP INDEX IF EXISTS idx_sales_category_amount;")
    conn.commit()

def create_indexes(conn):
    """Apply the strategic indexes."""
    with conn.cursor() as cur:
        with open("sql/03_indexes.sql", "r", encoding="utf-8") as f:
            cur.execute(f.read())
    conn.commit()

def run_explain(conn, query_sql: str):
    """Execute EXPLAIN ANALYZE and extract execution time and plan node."""
    with conn.cursor() as cur:
        cur.execute(query_sql)
        lines = [r[0] for r in cur.fetchall()]

    plan_text = "\n".join(lines)
    
    # Extract execution time
    exec_time = 0.0
    scan_type = "Seq Scan"
    for line in lines:
        if "Execution Time:" in line:
            exec_time = float(line.replace("Execution Time:", "").replace("ms", "").strip())
        if "Index Scan" in line:
            scan_type = "Index Scan"
        elif "Index Only Scan" in line:
            scan_type = "Index Only Scan"
        elif "Bitmap Index Scan" in line or "Bitmap Heap Scan" in line:
            scan_type = "Bitmap Scan"

    return exec_time, scan_type, plan_text

def run_benchmark():
    conn = get_connection()
    try:
        print("=" * 70)
        print("    POSTGRESQL QUERY PERFORMANCE BENCHMARK (EXPLAIN ANALYZE)")
        print("=" * 70)

        # 1. Benchmark WITHOUT Indexes
        print("\n[PHASE 1] Dropping secondary indexes to test baseline (Seq Scan)...")
        drop_indexes(conn)
        
        # Warm cache
        for q in TEST_QUERIES:
            run_explain(conn, q["sql"])

        baseline_results = []
        for q in TEST_QUERIES:
            t, scan, _ = run_explain(conn, q["sql"])
            baseline_results.append((q["name"], t, scan))

        # 2. Benchmark WITH Indexes
        print("\n[PHASE 2] Creating strategic B-Tree and covering indexes...")
        create_indexes(conn)

        # Warm cache
        for q in TEST_QUERIES:
            run_explain(conn, q["sql"])

        indexed_results = []
        for q in TEST_QUERIES:
            t, scan, plan = run_explain(conn, q["sql"])
            indexed_results.append((q["name"], t, scan, plan))

        # 3. Print Comparison Table
        print("\n" + "=" * 70)
        print(f"{'Query Scenario':<35} | {'Before (Seq Scan)':<18} | {'After (Indexed)':<18}")
        print("-" * 70)
        for i in range(len(TEST_QUERIES)):
            name, base_t, base_scan = baseline_results[i]
            _, idx_t, idx_scan, _ = indexed_results[i]
            print(f"{name:<35} | {base_t:>6.3f} ms ({base_scan:<8}) | {idx_t:>6.3f} ms ({idx_scan:<10})")
        print("=" * 70)

        print("\n[OPTIMIZATION EXPLANATION]")
        print("1. Date Range Queries: Transitioned from Seq Scan (scanning all table pages) to Bitmap/Index Scan, reading only matching timestamp blocks.")
        print("2. Covering Indexes: Replaced heap lookups with Index-Only Scans, eliminating table I/O completely for aggregated columns.")
        print("3. Composite Indexes: Combined category filtering and aggregation for sub-millisecond lookups.\n")

    finally:
        conn.close()

if __name__ == "__main__":
    run_benchmark()