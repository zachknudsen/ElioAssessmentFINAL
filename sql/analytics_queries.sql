-- 1. Top 10 customers by total sales

SELECT c.customer_id, c.customer_name, c.loyalty_segment, SUM(f.line_total) AS total_sales
FROM elio_gold.fact_sales f
JOIN elio_gold.dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.customer_id, c.customer_name, c.loyalty_segment
ORDER BY total_sales DESC
LIMIT 10;

-- 2. Monthly sales trend

SELECT DATE_TRUNC('month', order_date) AS month, SUM(line_total) AS total_sales, SUM(quantity) AS units_sold, COUNT(DISTINCT order_number) AS orders
FROM elio_gold.fact_sales
WHERE order_date IS NOT NULL
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month;

-- 3. Product sales outliers

WITH product_sales AS (
    SELECT p.product_id, p.product_name, p.product_category, SUM(f.line_total) AS total_sales
    FROM elio_gold.fact_sales f
    JOIN elio_gold.dim_product p ON f.product_id = p.product_id
    GROUP BY p.product_id, p.product_name, p.product_category
),

sales_stats AS (
    SELECT AVG(total_sales) AS mean_sales, STDDEV(total_sales) AS stddev_sales
    FROM product_sales
)

SELECT ps.product_id, ps.product_name, ps.product_category, ps.total_sales, ROUND((ps.total_sales - ss.mean_sales) / NULLIF(ss.stddev_sales, 0),2) AS sales_z_score
FROM product_sales ps
CROSS JOIN sales_stats ss
WHERE ABS((ps.total_sales - ss.mean_sales)/ NULLIF(ss.stddev_sales, 0)) >= 2
ORDER BY ABS(sales_z_score) DESC;

-- 4. Sales by state and loyalty segment

SELECT c.state, c.loyalty_segment, COUNT(DISTINCT c.customer_id) AS customers, COUNT(DISTINCT f.order_number) AS orders,
SUM(f.quantity) AS units_sold, SUM(f.line_total) AS total_sales
FROM elio_gold.fact_sales f
JOIN elio_gold.dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.state, c.loyalty_segment
ORDER BY total_sales DESC;

-- 5. Top 10 products in the latest month

WITH latest_month AS (
    SELECT DATE_TRUNC('month', MAX(order_date)) AS month
    FROM elio_gold.fact_sales
)

SELECT p.product_id, p.product_name, p.product_category, SUM(f.quantity) AS units_sold, SUM(f.line_total) AS total_sales
FROM elio_gold.fact_sales f
JOIN elio_gold.dim_product p ON f.product_id = p.product_id
CROSS JOIN latest_month lm
WHERE DATE_TRUNC('month', f.order_date) = lm.month
GROUP BY p.product_id, p.product_name, p.product_category
ORDER BY total_sales DESC
LIMIT 10;