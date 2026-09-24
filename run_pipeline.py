"""
run_pipeline.py
Main CLI execution script for the Associate Data Engineer ETL Pipeline.
Orchestrates: Extract -> Transform -> Validate -> Quarantine -> Load to PostgreSQL.
"""

import time
import argparse
from src.config import pipeline_config
from src.database import test_connection, apply_schema
from src.etl.extractor import extract_raw_data
from src.etl.transformer import transform_data
from src.etl.loader import load_clean_data, load_rejected_data

def run_etl_pipeline(raw_path: str = None, rejected_path: str = None):
    start_time = time.time()
    raw_path = raw_path or pipeline_config.raw_data_path
    rejected_path = rejected_path or pipeline_config.rejected_data_path

    print("=" * 65)
    print("      ASSOCIATE DATA ENGINEER ETL PIPELINE EXECUTION")
    print("=" * 65)

    # 1. Database Pre-flight Check
    print("\n[STEP 1/5] Verifying PostgreSQL connection and schema...")
    if not test_connection():
        print("[FATAL] Could not connect to PostgreSQL. Aborting pipeline.")
        return False
    apply_schema("sql/01_schema.sql")

    # 2. Extract Stage
    print("\n[STEP 2/5] Ingesting raw data source...")
    raw_df = extract_raw_data(raw_path)

    # 3. Transform & Validate Stage
    print("\n[STEP 3/5] Cleaning, standardizing, deduplicating & validating...")
    clean_df, rejected_df = transform_data(raw_df, rejected_output_path=rejected_path)

    # 4. Save Clean Local Parquet / CSV Artifact
    clean_df.to_csv(pipeline_config.processed_data_path, index=False)
    print(f"[PROCESS] Cleaned data backup saved to: {pipeline_config.processed_data_path}")

    # 5. Load Stage (PostgreSQL)
    print("\n[STEP 4/5] Bulk-loading clean records to PostgreSQL...")
    loaded_clean_count = load_clean_data(clean_df)

    print("\n[STEP 5/5] Ingesting rejected audit records to PostgreSQL...")
    load_rejected_data(rejected_df)

    elapsed_time = round(time.time() - start_time, 2)

    # Summary Report
    print("\n" + "=" * 65)
    print("               PIPELINE RUN SUMMARY REPORT")
    print("=" * 65)
    print(f"Total Raw Records Extracted:     {len(raw_df):,}")
    print(f"Total Quarantined / Rejected:    {len(rejected_df):,}")
    print(f"Total Clean Records Loaded to DB:{loaded_clean_count:,}")
    print(f"Success Ingestion Rate:          {round((loaded_clean_count / len(raw_df)) * 100, 2)}%")
    print(f"Total Execution Time:            {elapsed_time} seconds")
    print("=" * 65)
    print("[SUCCESS] ETL Pipeline completed successfully!\n")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Associate Data Engineer ETL Pipeline")
    parser.add_argument("--raw", type=str, default=None, help="Path to raw dataset")
    parser.add_argument("--rejected", type=str, default=None, help="Path to save rejected CSV")

    args = parser.parse_args()
    run_etl_pipeline(raw_path=args.raw, rejected_path=args.rejected)