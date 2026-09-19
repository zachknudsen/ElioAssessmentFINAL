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