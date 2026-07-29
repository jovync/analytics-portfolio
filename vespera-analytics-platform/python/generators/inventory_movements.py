"""
inventory_movements.py

Enterprise Inventory Movement Ledger

Builds the inventory movement history from
all operational business events.

Sources
-------
- Customer Sales      (negative quantity)
- Customer Returns     (positive quantity)
- Inbound Purchases    (positive quantity, from purchase_orders.py)

Future Sources
--------------
- Warehouse Transfers (DC -> Store internal replenishment)
- Manufacturing
- Stock Adjustments
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd

from config import RANDOM_SEED

from utils import generate_id

# --------------------------------------------------
# Movement Types
# --------------------------------------------------

CUSTOMER_SALE = "CUSTOMER_SALE"
CUSTOMER_RETURN = "CUSTOMER_RETURN"
INBOUND_PURCHASE = "INBOUND_PURCHASE"


# --------------------------------------------------
# Customer Sales
# --------------------------------------------------

def generate_sales_movements(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
) -> pd.DataFrame:

    merged = order_items_df.merge(

        orders_df[
            [
                "order_id",
                "order_date",
                "order_status",
                "fulfillment_warehouse_id",
            ]
        ],

        on="order_id",
        how="left",

    )

    merged = merged[merged["order_status"] == "Delivered"]

    records = []

    for i, row in enumerate(merged.itertuples(index=False), start=1):

        records.append({

            "movement_id":
                generate_id("MOV-SAL", i, width=8),

            "movement_date":
                pd.to_datetime(row.order_date) + timedelta(hours=2),

            "movement_type":
                CUSTOMER_SALE,

            "warehouse_id":
                row.fulfillment_warehouse_id,

            "product_id":
                row.product_id,

            "quantity":
                -int(row.quantity),

            "reference_type":
                "ORDER",

            "reference_id":
                row.order_id,

        })

    return pd.DataFrame(records)


# --------------------------------------------------
# Customer Returns
# --------------------------------------------------

def generate_return_movements(returns_df: pd.DataFrame) -> pd.DataFrame:

    records = []

    for i, row in enumerate(returns_df.itertuples(index=False), start=1):

        records.append({

            "movement_id":
                generate_id("MOV-RET", i, width=8),

            "movement_date":
                pd.to_datetime(row.return_date) + timedelta(hours=1),

            "movement_type":
                CUSTOMER_RETURN,

            "warehouse_id":
                row.warehouse_id,

            "product_id":
                row.product_id,

            "quantity":
                int(row.quantity),

            "reference_type":
                "RETURN",

            "reference_id":
                row.return_id,

        })

    return pd.DataFrame(records)


# --------------------------------------------------
# Inbound Purchases
# --------------------------------------------------

def generate_purchase_movements(
    purchase_orders_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Only POs that actually landed within the simulation window
    (po_status == "Received") generate a movement. "In Transit"
    POs represent stock that hasn't arrived yet as of simulation
    end and correctly have no ledger impact.
    """

    received = purchase_orders_df[
        purchase_orders_df["po_status"] == "Received"
    ]

    records = []

    for i, row in enumerate(received.itertuples(index=False), start=1):

        records.append({

            "movement_id":
                generate_id("MOV-PO", i, width=8),

            "movement_date":
                pd.to_datetime(row.actual_receipt_date)
                + timedelta(hours=6),

            "movement_type":
                INBOUND_PURCHASE,

            "warehouse_id":
                row.warehouse_id,

            "product_id":
                row.product_id,

            "quantity":
                int(row.quantity_received),

            "reference_type":
                "PURCHASE_ORDER",

            "reference_id":
                row.purchase_order_id,

        })

    return pd.DataFrame(records)


# --------------------------------------------------
# Master Generator
# --------------------------------------------------

def generate_inventory_movements(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    purchase_orders_df: pd.DataFrame,
) -> pd.DataFrame:

    sales = generate_sales_movements(orders_df, order_items_df)

    returns = generate_return_movements(returns_df)

    purchases = generate_purchase_movements(purchase_orders_df)

    movements = pd.concat(
        [sales, returns, purchases],
        ignore_index=True,
    )

    movements = (
        movements
        .sort_values("movement_date")
        .reset_index(drop=True)
    )

    return movements


# --------------------------------------------------
# Example
# --------------------------------------------------

if __name__ == "__main__":

    from customers import generate_customers
    from orders import generate_orders
    from order_items import generate_order_items
    from products import generate_products
    from purchase_orders import generate_purchase_orders
    from returns import generate_returns
    from shipments import generate_shipments
    from suppliers import generate_suppliers
    from warehouses import generate_warehouses

    suppliers_df = generate_suppliers()

    products_df = generate_products(suppliers_df=suppliers_df)

    customers_df = generate_customers()

    warehouses_df = generate_warehouses()

    orders_df = generate_orders(
        customers_df=customers_df,
        warehouses_df=warehouses_df,
    )

    order_items_df = generate_order_items(
        orders_df=orders_df,
        products_df=products_df,
    )

    shipments_df = generate_shipments(
        orders_df=orders_df,
        customers_df=customers_df,
        warehouses_df=warehouses_df,
    )

    returns_df = generate_returns(
        shipments_df=shipments_df,
        order_items_df=order_items_df,
        products_df=products_df,
    )

    purchase_orders_df = generate_purchase_orders(
        products_df=products_df,
        suppliers_df=suppliers_df,
        warehouses_df=warehouses_df,
    )

    inventory_movements_df = generate_inventory_movements(
        orders_df=orders_df,
        order_items_df=order_items_df,
        returns_df=returns_df,
        purchase_orders_df=purchase_orders_df,
    )

    print(
        f"{len(inventory_movements_df):,} inventory movements generated."
    )
    print()
    print(inventory_movements_df["movement_type"].value_counts())