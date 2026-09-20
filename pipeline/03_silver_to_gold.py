from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

# ============================================================
# Silver → Gold transformations
# ============================================================

# Gold model:
# - dim_customer: customer dimension with a surrogate key.
# - dim_product: product dimension using product_id as the
#   stable business key.
# - fact_sales: order-line fact table containing numeric
#   transaction metrics and foreign keys to the dimensions.
#
# Silver is kept normalized so customer/product/order data can
# be cleaned and conformed independently.
#
# Gold is deliberately denormalized into a star schema so
# analysts can query sales data with simpler joins and
# less join sprawl.

# ============================================================
# Customer Dimension
# ============================================================

customers = spark.table("elio_silver.customers")

# Create a surrogate key for each customer version.
# customer_id alone is not sufficient because customers can
# have multiple historical versions.
customer_window = Window.orderBy(
    F.col("customer_id"),
    F.col("valid_from")
)

dim_customer = (
    customers
    .withColumn(
        "customer_key",
        F.row_number().over(customer_window)
    )
    .select(
        "customer_key",
        "customer_id",
        "tax_id",
        "tax_code",
        "customer_name",
        "state",
        "city",
        "postcode",
        "street",
        "number",
        "unit",
        "region",
        "district",
        "lon",
        "lat",
        "ship_to_address",
        "valid_from",
        "valid_to",
        "units_purchased",
        "loyalty_segment",
        "_loaded_at",
        "_source"
    )
)

dim_customer.write.format("delta").mode("overwrite").saveAsTable(
    "elio_gold.dim_customer"
)

# ============================================================
# Product Dimension
# ============================================================

products = spark.table("elio_silver.products")

# product_id is already unique and stable in the source,
# so no additional surrogate key is required.
dim_product = (
    products
    .select(
        "product_id",
        "product_category",
        "product_name",
        "sales_price",
        "EAN13",
        "EAN5",
        "product_unit",
        "_loaded_at",
        "_source"
    )
)

dim_product.write.format("delta").mode("overwrite").saveAsTable(
    "elio_gold.dim_product"
)

# ============================================================
# Sales Fact
# ============================================================

sales_order_items = spark.table(
    "elio_silver.sales_order_items"
)

# Join each sales line to the customer version that was
# active when the order occurred.
customer_lookup = (
    dim_customer
    .select(
        "customer_key",
        "customer_id",
        "valid_from",
        "valid_to"
    )
)

fact_sales = (
    sales_order_items.alias("s")
    .join(
        customer_lookup.alias("c"),
        (
            (F.col("s.customer_id") == F.col("c.customer_id"))
            &
            (F.col("s.order_datetime") >= F.col("c.valid_from"))
            &
            (
                F.col("s.order_datetime")
                <= F.coalesce(
                    F.col("c.valid_to"),
                    F.to_timestamp(
                        F.lit("9999-12-31 23:59:59")
                    )
                )
            )
        ),
        "left"
    )
    .select(
        F.col("s.order_number"),
        F.col("s.line_number"),
        F.col("c.customer_key"),
        F.col("s.product_id"),
        F.col("s.order_datetime"),
        F.to_date(
            F.col("s.order_datetime")
        ).alias("order_date"),

        # Transaction metrics
        F.col("s.price"),
        F.col("s.quantity"),

        (
            F.col("s.price") * F.col("s.quantity")
        ).cast("decimal(18,2)").alias("line_total"),

        F.col("s.promo_disc"),
        F.col("s.promo_id"),
        F.col("s.promo_item"),
        F.col("s.promo_qty"),

        # Source currency/unit information
        F.col("s.currency"),
        F.col("s.unit"),

        # Metadata
        F.col("s._loaded_at"),
        F.col("s._source")
    )
)

fact_sales.write.format("delta").mode("overwrite").saveAsTable(
    "elio_gold.fact_sales"
)