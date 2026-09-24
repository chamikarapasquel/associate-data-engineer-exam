"""
tests/test_raw_dataset.py
Verifies Module 1 criteria for the raw dataset:
1. Row count >= 10,000
2. Required columns exist
3. Presence of nulls, duplicates, and formatting anomalies
"""

import csv
import os

RAW_DATA_PATH = "data/raw/raw_sales_data.csv"

def test_raw_dataset():
    assert os.path.exists(RAW_DATA_PATH), f"File {RAW_DATA_PATH} not found!"

    with open(RAW_DATA_PATH, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    total_rows = len(reader)
    print(f"\n--- Raw Dataset Quality Report ---")
    print(f"Total Rows Generated: {total_rows}")
    assert total_rows >= 10000, f"Expected at least 10,000 rows, got {total_rows}"

    # Verify column presence
    expected_cols = {
        "transaction_id", "customer_name", "category",
        "price", "quantity", "rating", "country", "created_date"
    }
    actual_cols = set(reader[0].keys())
    assert expected_cols.issubset(actual_cols), f"Missing columns: {expected_cols - actual_cols}"
    print(f"All 8 required columns verified: {sorted(list(actual_cols))}")

    # Count anomalies
    null_counts = {col: 0 for col in expected_cols}
    date_formats_found = set()
    negative_prices = 0
    currency_prices = 0
    invalid_ratings = 0
    seen_ids = set()
    duplicate_ids = 0

    for r in reader:
        # Check nulls
        for col in expected_cols:
            val = r[col]
            if val is None or val.strip() in ("", "None", "NULL"):
                null_counts[col] += 1

        # Check duplicates
        tid = r["transaction_id"]
        if tid in seen_ids:
            duplicate_ids += 1
        else:
            seen_ids.add(tid)

        # Check numeric anomalies
        price_val = str(r["price"]).strip()
        if price_val.startswith("$") or "," in price_val:
            currency_prices += 1
        elif price_val.startswith("-"):
            negative_prices += 1

        # Check ratings
        try:
            rating_float = float(r["rating"])
            if rating_float < 1.0 or rating_float > 5.0:
                invalid_ratings += 1
        except (ValueError, TypeError):
            if str(r["rating"]).strip() not in ("", "None", "NULL"):
                invalid_ratings += 1

    print("\n--- Detected Anomaly Breakdown ---")
    print(f"Duplicate Transaction IDs: {duplicate_ids}")
    print(f"Price currency strings: {currency_prices}")
    print(f"Negative prices: {negative_prices}")
    print(f"Invalid / out-of-range ratings: {invalid_ratings}")
    print(f"Null counts per column: {null_counts}")

    assert duplicate_ids > 0, "No duplicate records detected!"
    assert currency_prices > 0 or negative_prices > 0, "No price anomalies detected!"
    assert invalid_ratings > 0, "No rating anomalies detected!"
    assert any(c > 0 for c in null_counts.values()), "No missing values detected!"

    print("\n[SUCCESS] Module 1 Base Dataset passed all verification checks!")

if __name__ == "__main__":
    test_raw_dataset()