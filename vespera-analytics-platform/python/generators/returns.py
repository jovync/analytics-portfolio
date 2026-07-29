"""
Returns Generator

Creates enterprise customer return records for the
Vespera Analytics Platform.

Returns are generated from delivered shipments and
their corresponding order items.
"""

from __future__ import annotations

from datetime import timedelta
import random

import pandas as pd

from config import RANDOM_SEED, RETURN_REASONS

from utils import weighted_choice, generate_id

# =============================================================================
# CONFIGURATION
# =============================================================================

RETURN_DISPOSITION = {

    "Restock": 0.60,

    "Refurbish": 0.15,

    "Liquidate": 0.15,

    "Dispose": 0.10,

}


# =============================================================================
# GENERATOR
# =============================================================================

def generate_returns(
    shipments_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    products_df: pd.DataFrame,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate enterprise customer returns.

    Uses each product's own category-level return_rate (defined in
    PRODUCT_CATALOG, e.g. Apparel 12% vs. Personal Care 3%) rather
    than a single flat rate, so return likelihood actually varies
    by category as designed.
    """

    random.seed(seed)

    delivered_shipments = shipments_df[
        shipments_df["shipment_status"] == "Delivered"
    ].copy()

    # order_items_df carries its own warehouse_id (inherited from
    # the order header), which collides with shipments_df's
    # warehouse_id on merge. Drop it here since shipments_df's
    # copy is authoritative for "where this return physically
    # goes back to" — they're always the same warehouse in
    # practice, but keeping one source avoids the _x/_y suffix
    # pandas applies to colliding non-key columns.

    order_items_for_merge = order_items_df.drop(
        columns=["warehouse_id"]
    )

    merged = delivered_shipments.merge(
        order_items_for_merge,
        on="order_id",
        how="inner",
    )

    merged = merged.merge(
        products_df[["product_id", "return_rate"]],
        on="product_id",
        how="left",
    )

    records = []

    return_number = 1

    for _, row in merged.iterrows():

        if random.random() > row["return_rate"]:
            continue

        delivered_date = pd.to_datetime(row["delivered_date"])

        return_date = delivered_date + timedelta(
            days=random.randint(3, 30)
        )

        quantity = random.randint(1, int(row["quantity"]))

        disposition = weighted_choice(RETURN_DISPOSITION)

        records.append(

            {

                "return_id":
                    generate_id("RET", return_number, width=8),

                "order_id":
                    row["order_id"],

                "order_item_id":
                    row["order_item_id"],

                "shipment_id":
                    row["shipment_id"],

                "product_id":
                    row["product_id"],

                "warehouse_id":
                    row["warehouse_id"],

                "return_date":
                    return_date,

                "quantity":
                    quantity,

                "return_reason":
                    weighted_choice(RETURN_REASONS),

                "disposition":
                    disposition,

            }

        )

        return_number += 1

    returns_df = (
        pd.DataFrame(records)
        .sort_values("return_date")
        .reset_index(drop=True)
    )

    return returns_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    from customers import generate_customers
    from orders import generate_orders
    from order_items import generate_order_items
    from products import generate_products
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

    print(returns_df.head())
    print()
    print(returns_df.info())