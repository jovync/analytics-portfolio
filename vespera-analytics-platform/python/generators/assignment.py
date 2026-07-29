"""
Warehouse-Product Assignment

Determines which products are stocked/carried at which warehouses.
Computed ONCE and shared across inventory_snapshot.py,
purchase_orders.py, and order_items.py, so all three agree on
"does this warehouse carry this product."

Previously, inventory_snapshot.py and purchase_orders.py each
rolled independent random.random() decisions per (warehouse,
product) pair, so a warehouse could get opening stock but never
receive purchase orders for that same product (or vice versa) —
and order_items.py had no concept of warehouse assignment at all,
so it could sell products a warehouse never carried. That
combination is what caused persistent negative on-hand balances
that purchase-order quantity/cadence tuning alone couldn't fix.

High/Very High demand-tier products are always assigned to every
fulfillable warehouse, bypassing the probability — a real
retailer's best-sellers are stocked everywhere.
"""

from __future__ import annotations

import random

import pandas as pd

from config import RANDOM_SEED

WAREHOUSE_STOCKING_RULES = {

    "Distribution Center": 1.00,

    "Retail Store": 0.35,

    "Returns Center": 0.00,

}

ALWAYS_STOCK_TIERS = {"High", "Very High"}


def generate_product_warehouse_assignment(
    products_df: pd.DataFrame,
    warehouses_df: pd.DataFrame,
    demand_tiers: pd.Series,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate the master warehouse/product stocking assignment.

    Parameters
    ----------
    products_df
        Product master.

    warehouses_df
        Warehouse master.

    demand_tiers
        Output of utils.assign_demand_tiers(products_df). Index-
        aligned with products_df.

    seed
        Random seed for reproducible results.

    Returns
    -------
    pandas.DataFrame
        One row per (warehouse_id, product_id) pair that is
        actually stocked. Anything NOT in this table is not
        carried by that warehouse, and downstream generators
        (inventory_snapshot, purchase_orders, order_items) should
        never generate activity for warehouse/product combinations
        outside of it.
    """

    random.seed(seed)

    fulfillable = warehouses_df[
        warehouses_df["warehouse_type"] != "Returns Center"
    ]

    records = []

    for idx, product in products_df.iterrows():

        tier = demand_tiers.loc[idx]

        for _, warehouse in fulfillable.iterrows():

            warehouse_type = warehouse["warehouse_type"]

            probability = WAREHOUSE_STOCKING_RULES.get(
                warehouse_type,
                0.0,
            )

            stocked = (
                tier in ALWAYS_STOCK_TIERS
                or random.random() <= probability
            )

            if stocked:

                records.append(

                    {

                        "warehouse_id":
                            warehouse["warehouse_id"],

                        "product_id":
                            product["product_id"],

                    }

                )

    assignment_df = (
        pd.DataFrame(records)
        .sort_values(["warehouse_id", "product_id"])
        .reset_index(drop=True)
    )

    return assignment_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    from suppliers import generate_suppliers
    from products import generate_products
    from warehouses import generate_warehouses

    from utils import assign_demand_tiers

    suppliers_df = generate_suppliers()

    products_df = generate_products(suppliers_df=suppliers_df)

    warehouses_df = generate_warehouses()

    demand_tiers = assign_demand_tiers(products_df)

    assignment_df = generate_product_warehouse_assignment(
        products_df=products_df,
        warehouses_df=warehouses_df,
        demand_tiers=demand_tiers,
    )

    print(assignment_df.head())
    print()
    print(f"Total assignments: {len(assignment_df):,}")
    print()
    print(
        assignment_df.groupby("warehouse_id")["product_id"]
        .count()
        .rename("products_carried")
    )