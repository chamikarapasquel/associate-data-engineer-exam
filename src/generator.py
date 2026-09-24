"""
src/generator.py
Synthetic Raw Dataset Generator for Associate Data Engineer Examination.
Generates 10,000+ realistic e-commerce transaction records with intentional
data quality anomalies (missing values, mixed formats, duplicates, invalid ranges).
"""

import os
import csv
import random
import argparse
from datetime import datetime, timedelta

DEFAULT_SEED = 42

CATEGORIES = [
    "Electronics", "Home & Kitchen", "Apparel", "Books",
    "Sports & Outdoors", "Beauty & Personal Care", "Toys & Games", "Automotive"
]

COUNTRIES = [
    "United States", "Canada", "United Kingdom", "Germany",
    "France", "Australia", "Japan", "India", "Brazil", "Netherlands"
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"
]


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    """Generate a random datetime between start_date and end_date."""
    delta = end_date - start_date
    int_delta = int(delta.total_seconds())
    random_second = random.randint(0, int_delta)
    return start_date + timedelta(seconds=random_second)


def generate_clean_record(record_id: int) -> dict:
    """Generate a single clean transaction record."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    category = random.choice(CATEGORIES)
    country = random.choice(COUNTRIES)
    price = round(random.uniform(5.0, 1500.0), 2)
    quantity = random.randint(1, 8)
    rating = round(random.uniform(1.0, 5.0), 1)
    
    start_dt = datetime(2023, 1, 1)
    end_dt = datetime(2024, 12, 31, 23, 59, 59)
    created_dt = random_date(start_dt, end_dt)

    return {
        "transaction_id": f"TXN-{record_id:07d}",
        "customer_name": f"{first} {last}",
        "category": category,
        "price": price,
        "quantity": quantity,
        "rating": rating,
        "country": country,
        "created_date": created_dt.strftime("%Y-%m-%d %H:%M:%S")
    }


def inject_noise(record: dict) -> dict:
    """Inject intentional real-world anomalies into a clean record."""
    dirty = record.copy()
    rand_choice = random.random()

    # 1. Formatting Inconsistency - Dates (~15%)
    if rand_choice < 0.15:
        try:
            dt = datetime.strptime(dirty["created_date"], "%Y-%m-%d %H:%M:%S")
            date_format_choice = random.choice(["us_slash", "eu_slash", "dash", "text_month", "unix_epoch"])
            if date_format_choice == "us_slash":
                dirty["created_date"] = dt.strftime("%m/%d/%Y")
            elif date_format_choice == "eu_slash":
                dirty["created_date"] = dt.strftime("%d/%m/%Y")
            elif date_format_choice == "dash":
                dirty["created_date"] = dt.strftime("%d-%m-%Y")
            elif date_format_choice == "text_month":
                dirty["created_date"] = dt.strftime("%d-%b-%Y")
            elif date_format_choice == "unix_epoch":
                dirty["created_date"] = str(int(dt.timestamp()))
        except Exception:
            pass

    # 2. Casing & Whitespace Anomalies (~12%)
    if 0.15 <= rand_choice < 0.27:
        cat = dirty["category"]
        casing_variant = random.choice([
            cat.lower(),
            cat.upper(),
            f"  {cat}  ",
            cat.swapcase()
        ])
        dirty["category"] = casing_variant

    # 3. Country Inconsistencies (~10%)
    if 0.27 <= rand_choice < 0.37:
        country_map = {
            "United States": random.choice(["USA", "usa", "U.S.A.", "united states"]),
            "United Kingdom": random.choice(["UK", "uk", "U.K.", "great britain"]),
            "Canada": random.choice(["CAN", "can", "ca"]),
            "Germany": random.choice(["DEU", "de", "germany"]),
        }
        if dirty["country"] in country_map:
            dirty["country"] = country_map[dirty["country"]]

    # 4. Numeric Anomalies - Price (currency strings, negative values)
    if 0.37 <= rand_choice < 0.45:
        anomaly_type = random.choice(["currency_symbol", "negative", "comma_formatted"])
        p = dirty["price"]
        if anomaly_type == "currency_symbol":
            dirty["price"] = f"${p:,.2f}"
        elif anomaly_type == "comma_formatted":
            dirty["price"] = f"{p:,.2f}"
        elif anomaly_type == "negative":
            dirty["price"] = -p

    # 5. Rating Anomalies (out of range: < 1.0 or > 5.0, or text)
    if 0.45 <= rand_choice < 0.52:
        rating_anomaly = random.choice([0.0, -1.0, 6.5, 7.2, "Five", "N/A"])
        dirty["rating"] = rating_anomaly

    # 6. Missing Fields / Nulls
    if 0.52 <= rand_choice < 0.65:
        target_col = random.choice(["customer_name", "price", "rating", "country", "created_date", "quantity"])
        dirty[target_col] = random.choice(["", "NULL", "None", None])

    return dirty


def generate_dataset(num_records: int = 12500, output_path: str = "data/raw/raw_sales_data.csv", seed: int = DEFAULT_SEED):
    """Orchestrate dataset generation with clean, dirty, and duplicate records."""
    random.seed(seed)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Generating {num_records} base records with seed {seed}...")
    
    records = []
    for i in range(1, num_records + 1):
        clean_rec = generate_clean_record(i)
        dirty_rec = inject_noise(clean_rec)
        records.append(dirty_rec)

    # Inject Exact Duplicates (~3%)
    num_exact_dups = int(num_records * 0.03)
    print(f"Injecting {num_exact_dups} exact duplicate rows...")
    for _ in range(num_exact_dups):
        dup_record = random.choice(records).copy()
        records.append(dup_record)

    # Inject Logical Duplicates (~2% - same ID, altered attributes)
    num_logical_dups = int(num_records * 0.02)
    print(f"Injecting {num_logical_dups} logical duplicate rows (repeated ID)...")
    for _ in range(num_logical_dups):
        target = random.choice(records).copy()
        target["price"] = f"${round(random.uniform(10.0, 500.0), 2)}"
        target["created_date"] = "2024-12-31"
        records.append(target)

    random.shuffle(records)

    fieldnames = [
        "transaction_id", "customer_name", "category",
        "price", "quantity", "rating", "country", "created_date"
    ]

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    print(f"Successfully generated {len(records)} total records saved to: {output_path}")
    return output_path, len(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic raw dataset for Data Engineer Assessment")
    parser.add_argument("--records", type=int, default=12500, help="Number of base records to generate")
    parser.add_argument("--output", type=str, default="data/raw/raw_sales_data.csv", help="Output CSV path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()
    generate_dataset(num_records=args.records, output_path=args.output, seed=args.seed)