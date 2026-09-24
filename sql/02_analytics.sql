-- ============================================================================
-- sql/02_analytics.sql
-- 3 Analytical Queries for Associate Data Engineer Technical Examination
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Top 10 Categories by Revenue
-- Calculates total orders, total units sold, total revenue, average order value,
-- and percentage market share of total revenue across categories.
-- ----------------------------------------------------------------------------
SELECT 
    category,
    COUNT(*) AS total_orders,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS average_order_value,
    ROUND(SUM(total_amount) * 100.0 / SUM(SUM(total_amount)) OVER (), 2) AS revenue_share_pct
FROM sales_transactions
GROUP BY category
ORDER BY total_revenue DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- QUERY 2: Monthly Growth Analysis
-- Uses a Common Table Expression (CTE) and LAG() window function to calculate
-- Month-over-Month (MoM) revenue, absolute growth, and MoM growth rate percentage.
-- ----------------------------------------------------------------------------
WITH monthly_metrics AS (
    SELECT 
        DATE_TRUNC('month', created_date) AS sales_month,
        COUNT(*) AS total_transactions,
        SUM(quantity) AS total_units_sold,
        ROUND(SUM(total_amount), 2) AS current_month_revenue
    FROM sales_transactions
    GROUP BY DATE_TRUNC('month', created_date)
)
SELECT 
    TO_CHAR(sales_month, 'YYYY-MM') AS month_label,
    total_transactions,
    total_units_sold,
    current_month_revenue,
    LAG(current_month_revenue, 1) OVER (ORDER BY sales_month) AS prev_month_revenue,
    ROUND(current_month_revenue - LAG(current_month_revenue, 1) OVER (ORDER BY sales_month), 2) AS mom_growth_amount,
    ROUND(
        ((current_month_revenue - LAG(current_month_revenue, 1) OVER (ORDER BY sales_month)) 
         / NULLIF(LAG(current_month_revenue, 1) OVER (ORDER BY sales_month), 0)) * 100.0, 
        2
    ) AS mom_growth_pct
FROM monthly_metrics
ORDER BY sales_month;


-- ----------------------------------------------------------------------------
-- QUERY 3: Average Rating and Sales Metrics by Country
-- Demonstrates multi-dimensional aggregation across geographies:
-- Total revenue, order count, average rating, and customer satisfaction spread.
-- ----------------------------------------------------------------------------
SELECT 
    country,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS average_order_value,
    ROUND(AVG(rating), 2) AS avg_customer_rating,
    MIN(rating) AS min_rating,
    MAX(rating) AS max_rating
FROM sales_transactions
GROUP BY country
ORDER BY total_revenue DESC;