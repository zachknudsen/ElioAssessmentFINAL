### Part B — Analysis & Commercial Recommendation

#### B1) Commercial Insights

##### 1. Segment 3 drives most sales

Segment 3 has 1,342 customers and generates £9.60m in sales, compared with £734k across Segments 0–2. Segment 3 also averages 2.5 orders per customer, while the other segments are around 1 order per customer.

**Method:** Aggregated customers, orders and sales by loyalty segment.

**Why it matters:** Sales are heavily concentrated in Segment 3, making it the most relevant segment for retention and repeat-purchase activity.

##### 2. Repeat customers are disproportionately valuable, but highly skewed

There are 107 repeat customers compared with 1,820 one-time customers. Repeat customers generated £5.58m in sales versus £4.88m from one-time customers. However, repeat-customer value is highly skewed: the median repeat customer generated £7,692 in sales compared with a £52,145 average, with the top 25% exceeding £119k.

**Method:** Customers were classified as one-time or repeat based on their number of distinct orders, then customer-level sales were compared using both average and median values.

**Why it matters:** Repeat purchasing is associated with substantially higher sales, but the average is not representative of a typical repeat customer. This supports testing repeat-purchase conversion without assuming every converted customer will generate the same value as the highest-value repeat customers.

##### 3. Sales are concentrated across a few product categories

Zamaha, Rony and Opple are the three largest categories, generating £2.72m, £2.12m and £1.58m respectively. Together they account for approximately 62% of sales. Opple also has the highest sales per unit at £1,067.

**Method:** Aggregated sales and units sold by product category.

**Why it matters:** A small number of categories drive a large share of sales, which could be useful when selecting products for future campaigns. However, sales per unit should not be treated as profitability because cost data is not available.

---

#### B2) The Recommendation

##### Target

I would target the **1,243 Segment 3 customers who have purchased exactly once** with a second-purchase campaign.

##### Campaign

Offer **a percentage discount off a second purchase within 30 days**, with product recommendations based on their first purchase where possible. I would randomly split the target customers into treatment and control groups.

##### Expected impact

As a rough assumption, a 5 percentage-point incremental second-purchase rate would result in approximately 62 additional customers purchasing again.

Using the £3,349 average sales per Segment 3 one-time customer as an estimate of the value of a second order:

**62 × £3,349 ≈ £208k additional gross sales**

This is an illustrative estimate and does not account for discount costs or margin.

##### Measurement

Run the test for **8 weeks** and compare the second-purchase rate between treatment and control. I would also track incremental sales per customer, average order value and, if available, gross margin.

---

#### B3) Assumptions, Caveats & Data Quality

##### Assumptions and limitations

* `loyalty_segment` is treated as an existing business classification
* I used `state` rather than `region` because the raw region data contained inconsistent geographic values
* The 45 records with null `order_date` were retained in Gold but excluded from time-based analysis
* The sales source represents **order snapshots rather than a complete order-event history**. Gold uses the latest available version of each order, with `(order_number, line_number)` representing the sales-line grain. Repeat-purchase analysis is therefore based on the distinct final orders available
* The analysis is descriptive, not causal. In particular, higher sales among repeat customers does not prove that encouraging a second purchase will generate the same customer value
* Margin, acquisition channel, campaign exposure and inventory data were not available, so campaign ROI cannot be estimated directly

##### Production checks

1. Check `(order_number, line_number)` uniqueness and fact-table duplicates
2. Check that every `customer_key` and `product_id` in sales exists in the corresponding dimension tables, and check for invalid quantities or sales values
3. Monitor whether new data is arriving as expected, including `_loaded_at`, latest `order_date`, row volumes and unexpected nulls

I would detect silent schema changes using a schema contract or snapshot that checks for unexpected columns, removed fields or data-type changes. Stale data could be detected by monitoring `_loaded_at`, latest `order_date` and expected row volumes.

---

#### B4) Client Memo

This analysis takes raw ecommerce data through a Databricks Bronze, Silver, and Gold architecture, outputting reproducible customer, product, and sales tables for analysis.

The data suggests that Segment 3 drives the most sales, and that repeat customers generate substantially more value than one-time customers. Sales are also concentrated across a small number of product categories.

I recommend testing a second-purchase campaign targeting Segment 3 customers who have purchased once but have not yet returned. The campaign should use a randomized control group so we can measure incremental repeat purchases rather than assuming the offer caused the result.

The next step is an 8-week pilot, with second-purchase conversion and incremental sales as the main measures of success.

---

#### B5) LLM Use Case

A Genie Agent could provide a natural-language interface to the Gold tables.

For example:

> “Which loyalty segment generated the most sales, and how does its order frequency compare with the other segments?”

The agent would query the Gold tables and return the result in business language. Genie could also be used for anomaly detection purposes, sensing any schema changes, outliers, etc.

The main risks are incorrect calculations, hallucinations, inappropriate data access, and PII vulnerability. These could be reduced by limiting the agent to approved Gold tables, defining best practices and key metrics clearly, and validating generated queries and results.

Additionally, Genie could be used as a Github operator, a pipeline orchestrator, or even a visualization engine.
