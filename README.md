## **README**

### **A1: Bronze ingestion**

##### **Source:**  
Databricks `retail-org` sample dataset

##### **Datasets:**  
- customers
- products
- sales_orders

##### **Manual workspace steps:**

- Created the Unity Catalog schema: `workspace.elio_bronze`
- Connected the GitHub repository to Databricks
- Created and worked on the `feature/bronze-ingestion` branch
- Inspected the source directories to identify the source file formats
- Verified the resulting Bronze Delta tables after ingestion

##### **Runtime:**

- Spark version: `4.2.0`
- Databricks Free Edition

##### **Ingestion assumptions:**

- Customers is a comma-delimited CSV
- Products is a semicolon-delimited CSV
- Sales orders is JSON
- Spark schema inference is used for the Bronze load
- Source column names and nested structures are preserved
- Source data is loaded without business cleaning, deduplication, or transformations
- Spark-generated metadata files in the sales orders directory are not treated as source data

##### **Bronze tables:**

- `workspace.elio_bronze.customers`
- `workspace.elio_bronze.products`
- `workspace.elio_bronze.sales_orders`

### A2: Silver Layer

The Silver layer cleans and conforms the Bronze data while preserving information needed for downstream analytics.

- **Customers:** Customer records with the same `customer_id` can represent different versions of a customer. The `valid_from` and `valid_to` fields are retained so that customer history is not lost
- **Products:** Product records are type-conformed and retained at the source `product_id` grain
- **Sales order items:** Multiple records with the same `order_number` were identified as successive order snapshots. The latest snapshot is retained before `ordered_products` is exploded into individual product lines. The resulting natural key is `(order_number, line_number)`

Surrogate keys are introduced in the Gold dimensions rather than the
Silver layer. This allows the Silver layer to retain source/business
keys and historical customer versions while Gold provides warehouse
keys for dimensional modeling.

### A3: Data Modeling

The Silver layer is designed around a normalized logical model consisting
of Customers, Products, Sales Orders, and Sales Order Items.

The normalized model is documented in [`pipeline/data_model.md`](data_model.md),
including the entity relationships, primary and foreign keys, cardinality,
and 1NF/2NF/3NF rationale.

The model preserves historical customer versions using `valid_from` and
`valid_to`. The many-to-many relationship between sales orders and products
is resolved through `sales_order_items`.

The Gold layer subsequently reshapes this model into a dimensional model
with surrogate keys for analytical use.

### A4: Silver → Gold

The Silver layer contains normalized, conformed tables for customers, products, and sales order items. Data is cleaned, deduplicated, and enriched with `_loaded_at` and `_source` metadata.

The Gold layer deliberately denormalizes this data into a star schema for analytics:

- `dim_customer` — customer dimension with a surrogate `customer_key` and historical customer versions.
- `dim_product` — product dimension using the stable `product_id` business key.
- `fact_sales` — order-line fact table containing transaction metrics, order dates, customer keys, and product IDs.

Silver is normalized to keep data cleaning and conformance modular, while Gold uses a star schema to simplify analytical queries and reduce unnecessary joins.

### Data quality considerations

Some sales records contain missing `order_datetime` values, so a customer version cannot always be determined from the customer's historical validity period. In these cases, `customer_key` remains null rather than assigning an incorrect customer version.

A small number of records have valid order timestamps that fall into gaps between historical customer versions. These are also retained with a null `customer_key` because no valid customer version exists for the transaction date.