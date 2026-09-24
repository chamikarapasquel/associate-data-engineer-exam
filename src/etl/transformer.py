"""
src/etl/transformer.py
Core transformation engine:
- Cleans missing/null values
- Standardizes formats (multi-format dates, text casing, currency strings)
- Deduplicates exact and logical duplicate records
- Validates business constraints
- Logs rejected records with detailed rejection reasons
"""

import re
import os
import pandas as pd
from datetime import datetime
from dateutil import parser as date_parser

# Canonical country mapping dictionary
COUNTRY_NORMALIZATION_MAP = {
    "usa": "United States",
    "u.s.a.": "United States",
    "united states": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "united kingdom": "United Kingdom",
    "can": "Canada",
    "ca": "Canada",
    "canada": "Canada",
    "deu": "Germany",
    "de": "Germany",
    "germany": "Germany",
    "fra": "France",
    "france": "France",
    "aus": "Australia",
    "australia": "Australia",
    "jpn": "Japan",
    "japan": "Japan",
    "ind": "India",
    "india": "India",
    "bra": "Brazil",
    "brazil": "Brazil",
    "nld": "Netherlands",
    "netherlands": "Netherlands"
}


def parse_date_safely(date_val):
    """
    Standardize various date formats to ISO format (YYYY-MM-DD HH:MM:SS).
    Handles: ISO, US slash (MM/DD/YYYY), EU slash (DD/MM/YYYY), dashes, text months, unix epochs.
    """
    if pd.isna(date_val) or not str(date_val).strip() or str(date_val).strip() in ("None", "NULL", ""):
        return None

    s = str(date_val).strip()

    # Check for Unix Epoch Timestamp (e.g. 1726150809)
    if s.isdigit() and len(s) in (10, 13):
        try:
            epoch = int(s) if len(s) == 10 else int(s) / 1000
            return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    # Flexible date parsing
    try:
        parsed_dt = date_parser.parse(s)
        return parsed_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def clean_price(val):
    """Clean currency strings ($199.99, €50, commas) and return float or None."""
    if pd.isna(val) or not str(val).strip() or str(val).strip() in ("None", "NULL", ""):
        return None
    s = str(val).strip()
    # Remove currency signs and commas
    cleaned_str = re.sub(r"[^\d.-]", "", s)
    try:
        return float(cleaned_str)
    except ValueError:
        return None


def clean_quantity(val):
    """Clean quantity and return int or None."""
    if pd.isna(val) or not str(val).strip() or str(val).strip() in ("None", "NULL", ""):
        return None
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return None


def clean_rating(val):
    """Clean rating and return float or None."""
    if pd.isna(val) or not str(val).strip() or str(val).strip() in ("None", "NULL", ""):
        return None
    try:
        return round(float(str(val).strip()), 1)
    except (ValueError, TypeError):
        return None


def clean_text_field(val):
    """Strip whitespace and title-case text strings."""
    if pd.isna(val) or not str(val).strip() or str(val).strip() in ("None", "NULL", ""):
        return None
    return " ".join(str(val).strip().split()).title()


def normalize_country(val):
    """Normalize country abbreviations and casing to canonical full name."""
    if pd.isna(val) or not str(val).strip() or str(val).strip() in ("None", "NULL", ""):
        return None
    clean = str(val).strip().lower()
    return COUNTRY_NORMALIZATION_MAP.get(clean, clean.title())


def transform_data(raw_df: pd.DataFrame, rejected_output_path: str = "data/rejected/rejected_records.csv"):
    """
    Main transformation pipeline:
    1. Deduplicate exact duplicate rows
    2. Standardize formats (dates, strings, numbers)
    3. Validate business constraints
    4. Segregate clean vs rejected records
    5. Save quarantine logs
    """
    total_raw = len(raw_df)
    print(f"\n[TRANSFORM] Starting transformation on {total_raw:,} records...")

    # --- 1. Deduplicate Exact Rows ---
    df_dedup = raw_df.drop_duplicates().copy()
    exact_duplicates_count = total_raw - len(df_dedup)
    print(f"[TRANSFORM] Removed {exact_duplicates_count:,} exact duplicate rows.")

    # Storage for clean and rejected records
    clean_records = []
    rejected_records = []
    seen_transaction_ids = set()

    for _, row in df_dedup.iterrows():
        raw_row_dict = row.to_dict()
        tid = str(row.get("transaction_id", "")).strip()

        # Check: Missing Transaction ID
        if not tid or tid in ("None", "NULL", ""):
            raw_row_dict["rejection_reason"] = "MISSING_TRANSACTION_ID"
            rejected_records.append(raw_row_dict)
            continue

        # Check: Logical Duplicate (repeated transaction_id)
        if tid in seen_transaction_ids:
            raw_row_dict["rejection_reason"] = "DUPLICATE_TRANSACTION_ID"
            rejected_records.append(raw_row_dict)
            continue

        # Clean fields
        customer_name = clean_text_field(row.get("customer_name"))
        category = clean_text_field(row.get("category"))
        country = normalize_country(row.get("country"))
        price = clean_price(row.get("price"))
        quantity = clean_quantity(row.get("quantity"))
        rating = clean_rating(row.get("rating"))
        created_date = parse_date_safely(row.get("created_date"))

        # --- 2. Constraint Validations ---
        rejection_reasons = []

        if not customer_name:
            rejection_reasons.append("MISSING_CUSTOMER_NAME")

        if not category:
            rejection_reasons.append("MISSING_CATEGORY")

        if price is None:
            rejection_reasons.append("MISSING_OR_UNPARSEABLE_PRICE")
        elif price <= 0:
            rejection_reasons.append("INVALID_PRICE_NON_POSITIVE")

        if quantity is None:
            rejection_reasons.append("MISSING_OR_UNPARSEABLE_QUANTITY")
        elif quantity <= 0:
            rejection_reasons.append("INVALID_QUANTITY_NON_POSITIVE")

        if rating is None:
            rejection_reasons.append("MISSING_OR_UNPARSEABLE_RATING")
        elif rating < 1.0 or rating > 5.0:
            rejection_reasons.append("RATING_OUT_OF_BOUNDS")

        if not country:
            rejection_reasons.append("MISSING_OR_INVALID_COUNTRY")

        if not created_date:
            rejection_reasons.append("MISSING_OR_UNPARSEABLE_DATE")

        # If any validation failed, quarantine to rejected
        if rejection_reasons:
            raw_row_dict["rejection_reason"] = "; ".join(rejection_reasons)
            rejected_records.append(raw_row_dict)
        else:
            # Mark ID as seen and add to clean records
            seen_transaction_ids.add(tid)
            total_amount = round(price * quantity, 2)
            clean_records.append({
                "transaction_id": tid,
                "customer_name": customer_name,
                "category": category,
                "price": price,
                "quantity": quantity,
                "total_amount": total_amount,
                "rating": rating,
                "country": country,
                "created_date": created_date
            })

    # Convert to DataFrames
    clean_df = pd.DataFrame(clean_records)
    rejected_df = pd.DataFrame(rejected_records)

    # --- 3. Save Quarantined Records to CSV ---
    os.makedirs(os.path.dirname(rejected_output_path), exist_ok=True)
    rejected_df.to_csv(rejected_output_path, index=False)
    print(f"[TRANSFORM] Quarantined {len(rejected_df):,} rejected records saved to: {rejected_output_path}")

    # Breakdown of top rejection reasons
    if not rejected_df.empty:
        print("[TRANSFORM] Top Rejection Reasons:")
        print(rejected_df["rejection_reason"].value_counts().head(5).to_string())

    print(f"[TRANSFORM] Cleaned & Validated Records Ready for Loading: {len(clean_df):,}")
    return clean_df, rejected_df