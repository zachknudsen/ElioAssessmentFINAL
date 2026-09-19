# Elio Technical Assessment: Zachary Knudsen

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

spark.sql("""
CREATE SCHEMA IF NOT EXISTS elio_bronze
""")

# Customers
customers_df = spark.read.csv(
    "/databricks-datasets/retail-org/customers/customers.csv",
    header=True,
    inferSchema=True
)

customers_df.write.format("delta").mode("overwrite").saveAsTable(
    "elio_bronze.customers"
)

# Products
products_df = spark.read.csv(
    "/databricks-datasets/retail-org/products/products.csv",
    header=True,
    inferSchema=True,
    sep=";"
)

products_df.write.format("delta").mode("overwrite").saveAsTable(
    "elio_bronze.products"
)

# Sales Orders
sales_orders_df = spark.read.json(
    "/databricks-datasets/retail-org/sales_orders/"
)

sales_orders_df.write.format("delta").mode("overwrite").saveAsTable(
    "elio_bronze.sales_orders"
)