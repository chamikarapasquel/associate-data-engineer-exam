-- sql/01_schema.sql
-- Table definitions, primary keys, constraints, and audit tables

-- 1. Main Cleaned Transactions Table
CREATE TABLE IF NOT EXISTS sales_transactions (
    transaction_id VARCHAR(32) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price > 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    total_amount NUMERIC(12, 2) NOT NULL CHECK (total_amount > 0),
    rating NUMERIC(2, 1) NOT NULL CHECK (rating >= 1.0 AND rating <= 5.0),
    country VARCHAR(50) NOT NULL,
    created_date TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Quarantined / Rejected Records Audit Table
CREATE TABLE IF NOT EXISTS rejected_records_log (
    rejection_id SERIAL PRIMARY KEY,
    raw_transaction_id VARCHAR(64),
    rejection_reason VARCHAR(255) NOT NULL,
    customer_name VARCHAR(100),
    category VARCHAR(50),
    price VARCHAR(50),
    quantity VARCHAR(50),
    rating VARCHAR(50),
    country VARCHAR(50),
    created_date VARCHAR(50),
    rejected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);