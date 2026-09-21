## **README**

### Databricks Setup

* **Platform:** Databricks Free Edition
* **Spark runtime:** `4.2.0`
* **Bronze schema:** `elio_bronze`
* **Silver schema:** `elio_silver`
* **Gold schema:** `elio_gold`

### How to Run

The pipeline can be reproduced in the following order:

1. Run `ingest/load_bronze.py` to create the Bronze tables.
2. Run `pipeline/01_create_tables.sql` to create the required schemas/tables.
3. Run `pipeline/02_bronze_to_silver.py` to build the Silver tables.
4. Run `pipeline/03_silver_to_gold.py` to build the Gold tables.
5. Run `sql/analytics_queries.sql` to execute the required analytics queries.

Note: Step 2 only needs to be run once to create the Silver and Gold Spark tables.

A Databricks Job was also created to provide a repeatable workflow for running the pipeline and its transformations.

### Repository Structure

```text
ingest/
    load_bronze.py

pipeline/
    01_create_tables.sql
    02_bronze_to_silver.py
    03_silver_to_gold.py
    data_model.md

sql/
    analytics_queries.sql
    analysis_answers.md
```

The GitHub repository is connected to Databricks through a Databricks Git folder. Development was performed on multiple branches, with the repository providing version control for the ingestion code, bronze -> silver -> gold transformations, SQL queries, and data model documentation.

### Time-box Assumptions and Shortcuts

Given the time-boxed nature of the assessment:

* The pipeline uses full-refresh processing rather than an incremental ingestion framework.
* Spark schema inference is used for Bronze ingestion rather than maintaining explicit source schemas.
* The current implementation uses Databricks Free Edition rather than separate development and production environments.
* Automated CI/CD, DLT/dbt, and production deployment infrastructure were not implemented.
* Production-oriented approaches such as incremental `MERGE` processing and separate development/production catalogs are documented where relevant rather than implemented.

# **STEP BY STEP INSTRUCTIONS**

### **A1: Bronze ingestion**

##### **Source:**  
Databricks `retail-org` sample dataset - 
this source was utilized per the instructions of the assignment.

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

##### **Ingestion assumptions:**

- Customers is a comma-delimited CSV
- Products is a semicolon-delimited CSV
- Sales orders is JSON
- Source column names and nested structures are preserved
- Source data is loaded without business cleaning, deduplication, or transformations
- Spark-generated metadata files in the sales orders directory are not treated as source data

##### **Bronze tables:**

- `elio_bronze.customers`
- `elio_bronze.products`
- `elio_bronze.sales_orders`

### **A2: Silver Layer**

The Silver layer cleans and conforms the Bronze data while preserving information needed for downstream analytics.

- **Customers:** Customer records with the same `customer_id` can represent different versions of a customer. The `valid_from` and `valid_to` fields are retained so that customer history is not lost
- **Products:** Product records are type-conformed and retained at the source `product_id` grain
- **Sales order items:** Multiple records with the same `order_number` were identified as successive order snapshots. The latest snapshot is retained before `ordered_products` is exploded into individual product lines. The resulting natural key is `(order_number, line_number)`

Surrogate keys are introduced in the Gold dimensions rather than the Silver layer. This allows the Silver layer to retain source/business keys and historical customer versions while Gold provides warehouse keys for dimensional modeling.

### **A3: Data Modeling**

The Silver layer is designed around a normalized logical model consisting of Customers, Products, Sales Orders, and Sales Order Items.

The normalized model is documented in [`pipeline/data_model.md`](pipeline/data_model.md), including the entity relationships, primary and foreign keys, cardinality, and 1NF/2NF/3NF rationale.

The model preserves historical customer versions using `valid_from` and `valid_to`. The many-to-many relationship between sales orders and products is resolved through `sales_order_items`.

The Gold layer subsequently reshapes this model into a dimensional model with surrogate keys for analytical use.

### **A4: Silver → Gold**

Silver data is cleaned, deduplicated, and enriched with `_loaded_at` and `_source` metadata.

The Gold layer deliberately denormalizes this data into a star schema for analytics (simplifying queries and reducing unnecessary joins):

- `dim_customer` — customer dimension with a surrogate `customer_key` and historical customer versions.
- `dim_product` — product dimension using the stable `product_id` business key.
- `fact_sales` — order-line fact table containing transaction metrics, order dates, customer keys, and product IDs.

### Data quality considerations

Some sales records contain missing `order_datetime` values, so a customer version cannot always be determined from the customer's historical validity period. In these cases, `customer_key` remains null rather than assigning an incorrect customer version.

A small number of records have valid order timestamps that fall into gaps between historical customer versions. These are also retained with a null `customer_key` because no valid customer version exists for the transaction date.

### **A5: Analytics SQL Queries**

The five required analytics queries were completed against the Gold-layer tables.

The queries cover:

1. **Top 10 customers by sales**
2. **Monthly sales trend**
3. **Product sales outliers**
4. **Sales by state and loyalty segment**
5. **Top 10 products in the latest available month**

The SQL queries are stored in the repository under `sql/`.

### **Part B: Analysis & Commercial Recommendation**

Commercial analysis and recommendations are documented separately in the Part B analysis file.

At a high level, the analysis identifies differences in customer segment value, purchasing behaviour, product performance, and sales across geography and loyalty segments.

### **Part C: Productionisation**

#### Pipeline Orchestration

A Databricks Job was created using **Databricks Genie** to provide a repeatable workflow for running the pipeline and its transformations.

#### Idempotency

The pipeline uses full-refresh `overwrite` semantics for the Bronze, Silver, and Gold outputs. Rerunning the pipeline replaces the existing output tables rather than appending another copy of the same records.

For a future incremental implementation, `MERGE` could be used with appropriate business keys to update existing records and insert new records.

#### Development and Production Separation

For a production implementation, development and production data would be separated using different Unity Catalog catalogs or schemas.

For example:

```text
dev.elio_bronze
dev.elio_silver
dev.elio_gold

prod.elio_bronze
prod.elio_silver
prod.elio_gold
```

Development changes would be tested against the `dev` environment before the validated pipeline is deployed to `prod`, preventing development runs from modifying production data.

The current assessment uses the `workspace` catalog in Databricks Free Edition, so this environment separation is documented as a production design rather than implemented as separate production infrastructure.

### Final LLM Experimentation/Use Case

A separate Genie agent was also created and connected directly to the Gold datasets. The agent can answer questions about the underlying business data directly, providing an accessible natural-language interface to the analytical data without requiring users to write SQL queries.
