from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

# Bronze → Silver transformations

# Customers:
# - Preserve all customer versions from Bronze.
# - Cast fields to appropriate data types.
# - valid_from / valid_to are retained to preserve customer history.

# Products:
# - Cast numeric fields to appropriate data types.
# - Product records are retained as product_id is unique in the source.

# Sales orders:
# - Multiple records with the same order_number represent successive
#   snapshots of an order.
# - Retain the latest snapshot for each order_number.
# - Explode ordered_products into one row per product line.
# - Use order_number + line_number as the Silver natural key.

# Customers
customers = spark.table("elio_bronze.customers")

customers_silver = (
    customers
    .withColumn("customer_id", F.col("customer_id").cast("int"))
    .withColumn("tax_id", F.col("tax_id").cast("double"))
    .withColumn("units_purchased", F.col("units_purchased").cast("int"))
    .withColumn("loyalty_segment", F.col("loyalty_segment").cast("int"))
)

customers_silver.write.format("delta").mode("overwrite").saveAsTable(
    "elio_silver.customers"
)

# Products
products = spark.table("elio_bronze.products")

products_silver = (
    products
    .withColumn(
        "sales_price",
        F.expr("try_cast(sales_price AS DECIMAL(18,2))")
    )
    .withColumn("EAN13", F.col("EAN13").cast("long"))
    .withColumn("EAN5", F.col("EAN5").cast("int"))
)

products_silver.write.format("delta").mode("overwrite").saveAsTable(
    "elio_silver.products"
)

# Sales Orders
sales_orders = spark.table("elio_bronze.sales_orders")

# Keep the latest snapshot for each order
window = Window.partitionBy("order_number").orderBy(
    F.col("order_datetime").desc()
)

latest_orders = (
    sales_orders
    .withColumn("snapshot_rank", F.row_number().over(window))
    .filter(F.col("snapshot_rank") == 1)
    .drop("snapshot_rank")
)

# Explode the latest order snapshot into product lines
sales_order_items = (
    latest_orders
    .select(
        "order_number",
        "customer_id",
        "customer_name",
        "order_datetime",
        F.posexplode("ordered_products").alias(
            "line_number",
            "ordered_product"
        )
    )
    .select(
        "order_number",

        # Make line numbers start at 1
        (F.col("line_number") + 1).cast("int").alias("line_number"),

        F.col("customer_id").cast("int").alias("customer_id"),
        F.col("customer_name").alias("customer_name"),

        F.from_unixtime(
            F.expr("try_cast(NULLIF(order_datetime, '') AS BIGINT)")
        ).cast("timestamp").alias("order_datetime"),

        F.col("ordered_product.id").alias("product_id"),
        F.col("ordered_product.name").alias("product_name"),
        F.col("ordered_product.curr").alias("currency"),

        F.expr(
            "try_cast(ordered_product.price AS DECIMAL(18,2))"
        ).alias("price"),

        F.expr(
            "try_cast(ordered_product.qty AS INT)"
        ).alias("quantity"),

        F.col("ordered_product.unit").alias("unit"),

        F.expr(
            "try_cast(ordered_product.promotion_info.promo_disc AS DECIMAL(18,2))"
        ).alias("promo_disc"),

        F.expr(
            "try_cast(ordered_product.promotion_info.promo_id AS BIGINT)"
        ).alias("promo_id"),

        F.col("ordered_product.promotion_info.promo_item")
            .alias("promo_item"),

        F.expr(
            "try_cast(ordered_product.promotion_info.promo_qty AS INT)"
        ).alias("promo_qty")
    )
)

sales_order_items.write.format("delta").mode("overwrite").saveAsTable(
    "elio_silver.sales_order_items"
)