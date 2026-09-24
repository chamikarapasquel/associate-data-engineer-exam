-- ============================================================================
-- sql/03_indexes.sql
-- Strategic Indexes for Performance Optimization
-- ============================================================================

-- 1. B-Tree Index for Time-Series & Date Range Scans
-- Rationale: Enables Bitmap Index Scan or Index Scan for date filters,
-- avoiding reading all disk blocks sequentially.
CREATE INDEX IF NOT EXISTS idx_sales_created_date 
ON sales_transactions (created_date);

-- 2. Composite Covering Index for Country Metrics (Index-Only Scan)
-- Rationale: By including (rating, total_amount) in the leaf pages,
-- PostgreSQL can fulfill analytical aggregates without touching table heap pages.
CREATE INDEX IF NOT EXISTS idx_sales_country_covering 
ON sales_transactions (country) 
INCLUDE (rating, total_amount);

-- 3. Composite Index for Category Filtering & Revenue Sorting
-- Rationale: Optimizes queries filtering by category and aggregating revenue.
CREATE INDEX IF NOT EXISTS idx_sales_category_amount 
ON sales_transactions (category, total_amount);