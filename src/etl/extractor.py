"""
src/etl/extractor.py
Extracts raw transaction datasets from storage (local CSV or S3).
"""

import os
import pandas as pd

def extract_raw_data(file_path: str = "data/raw/raw_sales_data.csv") -> pd.DataFrame:
    """Read raw CSV file and return as pandas DataFrame."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file not found at: {file_path}")

    # Read all columns as strings initially to preserve raw values for audit/cleaning
    df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    print(f"[EXTRACT] Successfully extracted {len(df):,} raw records from {file_path}")
    return df