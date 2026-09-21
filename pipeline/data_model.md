## A3 - Normalised Data Model

### 3NF Logical Model

The Silver layer is modeled into four logical entities:

#### Customer

| Attribute | Key |
|---|---|
| customer_id | PK |
| customer_name | |
| tax_id | |
| tax_code | |
| state | |
| city | |
| postcode | |
| street | |
| number | |
| unit | |
| region | |
| district | |
| lon | |
| lat | |
| ship_to_address | |
| valid_from | (PK)|
| valid_to | (PK)|
| units_purchased | |
| loyalty_segment | |

Customer versions are retained using `valid_from` and `valid_to`.

The composite LOGICAL key for Customer is (customer_id, valid_from, valid_to), representing the customer and its validity period.

#### Product

| Attribute | Key |
|---|---|
| product_id | PK |
| product_category | |
| product_name | |
| sales_price | |
| EAN13 | |
| EAN5 | |
| product_unit | |

#### Sales Order

| Attribute | Key |
|---|---|
| order_number | PK |
| customer_id | FK → Customer.customer_id |
| order_datetime | |

#### Sales Order Item

| Attribute | Key |
|---|---|
| order_number | PK/FK → Sales Order.order_number |
| line_number | PK |
| product_id | FK → Product.product_id |
| currency | |
| price | |
| quantity | |
| unit | |
| promo_disc | |
| promo_id | |
| promo_item | |
| promo_qty | |

The composite primary key for Sales Order Item is `(order_number, line_number)`.

### ERD / Relationships

| Entity | Relationship | Entity | Cardinality |
|---|---|---|---|
| Customer | places | Sales Order | 1 : many |
| Sales Order | contains | Sales Order Item | 1 : many |
| Product | appears in | Sales Order Item | 1 : many |

#### Keys and Foreign Keys

| Entity | Primary Key | Foreign Keys |
|---|---|---|
| Customer | `customer_id`, `valid_from`, `valid_to` | — |
| Product | `product_id` | — |
| Sales Order | `order_number` | `customer_id` → Customer |
| Sales Order Item | `(order_number, line_number)` | `order_number` → Sales Order, `product_id` → Product |

The `Sales Order Item` entity resolves the many-to-many relationship between
Sales Orders and Products: an order can contain multiple products, while a
product can appear in multiple orders.

### Normalisation Rationale

#### First Normal Form (1NF)

The model contains atomic attributes and no repeating groups. The nested
`ordered_products` array from the Bronze sales order data is resolved
into individual rows in `SALES_ORDER_ITEM`, with one row per order line.

#### Second Normal Form (2NF)

All non-key attributes depend on the full primary key. `SALES_ORDER_ITEM`
uses the composite key `(order_number, line_number)`, so line-level
attributes such as price, quantity and promotion information describe the
specific order line. Order-level attributes are stored in `SALES_ORDER`,
while product-level attributes are stored in `PRODUCT`.

#### Third Normal Form (3NF)

Non-key attributes depend only on the key of their respective entity.
Customer attributes are stored in `CUSTOMER`, product attributes are stored
in `PRODUCT`, and order attributes are stored in `SALES_ORDER`. This avoids
storing attributes such as `customer_name` or `product_name` redundantly in
downstream entities.

#### Many-to-Many Relationship

An order can contain multiple products, and a product can appear in
multiple orders. This many-to-many relationship is resolved through
`SALES_ORDER_ITEM`, which acts as the associative entity between
`SALES_ORDER` and `PRODUCT`.

#### Deliberate Denormalisation

No deliberate denormalisation is introduced in this logical 3NF model.
Analytical denormalisation is introduced later in the Gold layer, where
dimensions and facts are designed for analytical querying.