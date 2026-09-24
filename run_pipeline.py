"""
run_pipeline.py
Main CLI execution script for the Associate Data Engineer ETL Pipeline.
Orchestrates: 
  1. PostgreSQL Pre-flight & Schema Verification
  2. Raw Data Extraction
  3. Transformation, Cleansing, Deduplication & Validation
  4. Quarantining Rejected Records
  5. Bulk-loading Clean Records to PostgreSQL
  6. (Optional) AWS S3 Cloud Synchronization
"""

import time
import argparse
from src.config import pipeline_config
from src.database import test_connection, apply_schema
from src.etl.extractor import extract_raw_data
from src.etl.transformer import transform_data
from src.etl.loader import load_clean_data, load_rejected_data
from src.s3_service import S3Service

def run_etl_pipeline(raw_path: str = None, rejected_path: str = None, sync_s3: bool = False):
    start_time = time.time()
    raw_path = raw_path or pipeline_config.raw_data_path
    rejected_path = rejected_path or pipeline_config.rejected_data_path

    print("=" * 65)
    print("      ASSOCIATE DATA ENGINEER ETL PIPELINE EXECUTION")
    print("=" * 65)

    # 1. Database Pre-flight Check
    print("\n[STEP 1/6] Verifying PostgreSQL connection and schema...")
    if not test_connection():
        print("[FATAL] Could not connect to PostgreSQL. Aborting pipeline.")
        return False
    apply_schema("sql/01_schema.sql")

    # 2. Extract Stage
    print("\n[STEP 2/6] Ingesting raw data source...")
    raw_df = extract_raw_data(raw_path)

    # 3. Transform & Validate Stage
    print("\n[STEP 3/6] Cleaning, standardizing, deduplicating & validating...")
    clean_df, rejected_df = transform_data(raw_df, rejected_output_path=rejected_path)

    # 4. Save Clean Local Output Artifact
    clean_df.to_csv(pipeline_config.processed_data_path, index=False)
    print(f"[PROCESS] Cleaned data backup saved to: {pipeline_config.processed_data_path}")

    # 5. Load Stage (PostgreSQL)
    print("\n[STEP 4/6] Bulk-loading clean records to PostgreSQL...")
    loaded_clean_count = load_clean_data(clean_df)

    print("\n[STEP 5/6] Ingesting rejected audit records to PostgreSQL...")
    load_rejected_data(rejected_df)

    # 6. AWS S3 Synchronization (Page 2 Requirement)
    if sync_s3:
        print("\n[STEP 6/6] Synchronizing pipeline artifacts with AWS S3...")
        s3 = S3Service()
        s3.sync_all_artifacts(
            raw_path=raw_path,
            processed_path=pipeline_config.processed_data_path,
            rejected_path=rejected_path
        )
    else:
        print("\n[STEP 6/6] AWS S3 sync skipped (pass --sync-s3 to enable).")

    elapsed_time = round(time.time() - start_time, 2)

    # Summary Report
    print("\n" + "=" * 65)
    print("               PIPELINE RUN SUMMARY REPORT")
    print("=" * 65)
    print(f"Total Raw Records Extracted:     {len(raw_df):,}")
    print(f"Total Quarantined / Rejected:    {len(rejected_df):,}")
    print(f"Total Clean Records Loaded to DB:{loaded_clean_count:,}")
    print(f"Success Ingestion Rate:          {round((loaded_clean_count / len(raw_df)) * 100, 2)}%")
    print(f"AWS S3 Cloud Sync:               {'COMPLETED' if sync_s3 else 'SKIPPED'}")
    print(f"Total Execution Time:            {elapsed_time} seconds")
    print("=" * 65)
    print("[SUCCESS] ETL Pipeline completed successfully!\n")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Associate Data Engineer ETL Pipeline")
    parser.add_argument("--raw", type=str, default=None, help="Path to raw dataset")
    parser.add_argument("--rejected", type=str, default=None, help="Path to save rejected CSV")
    parser.add_argument("--sync-s3", action="store_true", help="Synchronize raw, clean, and backup artifacts to AWS S3")

    args = parser.parse_args()
    run_etl_pipeline(raw_path=args.raw, rejected_path=args.rejected, sync_s3=args.sync_s3)