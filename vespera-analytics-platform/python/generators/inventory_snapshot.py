"""
Inventory Snapshot Generator

Creates the opening inventory position for the
Vespera Analytics Platform.

Each record represents the inventory position of one
product within one fulfillment location at the start
of the simulation.

Which (warehouse, product) pairs get an opening snapshot is driven
entirely by assignment_df — the same shared assignment table used
by purchase_orders.py and order_items.py — instead of this file
rolling its own independent stocking probability.

Only products already launched as of the snapshot date are
included — products launching later receive their first stock via
an "Inbound Purchase" movement around their launch date in
inventory_movements.py instead.
"""

from __future__ import annotations

import random

import pandas as pd

from config import (
    RANDOM_SEED,
    SIMULATION_START_DATE,
)

from utils import generate_id

# =============================================================================
# CONFIGURATION
# =============================================================================

MIN_DC_STOCK = 100
MAX_DC_STOCK = 750

MIN_STORE_STOCK = 5
MAX_STORE_STOCK = 75

SAFETY_STOCK_PERCENT = (
    0.10,
    0.25,
)

RESERVED_PERCENT = (
    0.02,
    0.10,
)

# =============================================================================
# GENERATOR
# =============================================================================

def generate_inventory_snapshot(
    products_df: pd.DataFrame,
    warehouses_df: pd.DataFrame,
    assignment_df: pd.DataFrame,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate the enterprise opening inventory snapshot.

    Parameters
    ----------
    products_df
        Product master.

    warehouses_df
        Warehouse master.

    assignment_df
        Output of assignment.generate_product_warehouse_assignment().
        Defines exactly which (warehouse_id, product_id) pairs are
        eligible for an opening snapshot row.

    seed
        Random seed for reproducible results.

    Returns
    -------
    pandas.DataFrame
    """

    random.seed(seed)

    snapshot_date = SIMULATION_START_DATE.date()

    # ----------------------------------------------------------
    # Only stock products that have actually launched as of the
    # snapshot date. Products with launch_date later than day one
    # of the simulation get no opening inventory.
    # ----------------------------------------------------------

    launched_products_df = products_df[
        products_df["launch_date"] <= snapshot_date
    ]

    eligible_pairs = assignment_df.merge(
        launched_products_df[["product_id"]],
        on="product_id",
        how="inner",
    )

    warehouse_type_lookup = warehouses_df.set_index(
        "warehouse_id"
    )["warehouse_type"].to_dict()

    product_lookup = launched_products_df.set_index("product_id")

    records = []

    snapshot_number = 1

    for _, pair in eligible_pairs.iterrows():

        warehouse_id = pair["warehouse_id"]
        product_id = pair["product_id"]

        warehouse_type = warehouse_type_lookup[warehouse_id]
        product = product_lookup.loc[product_id]

        if warehouse_type == "Distribution Center":

            quantity_on_hand = random.randint(
                MIN_DC_STOCK,
                MAX_DC_STOCK,
            )

        else:

            quantity_on_hand = random.randint(
                MIN_STORE_STOCK,
                MAX_STORE_STOCK,
            )

        quantity_reserved = int(
            quantity_on_hand
            * random.uniform(*RESERVED_PERCENT)
        )

        quantity_available = (
            quantity_on_hand - quantity_reserved
        )

        safety_stock = int(
            quantity_on_hand
            * random.uniform(*SAFETY_STOCK_PERCENT)
        )

        reorder_point = max(
            safety_stock * 2,
            product["reorder_point"],
        )

        inventory_value = round(
            quantity_on_hand * product["base_cost_sgd"],
            2,
        )

        records.append(

            {

                "inventory_snapshot_id":
                    generate_id("INVSNAP", snapshot_number, width=7),

                "snapshot_date":
                    snapshot_date,

                "warehouse_id":
                    warehouse_id,

                "product_id":
                    product_id,

                "quantity_on_hand":
                    quantity_on_hand,

                "quantity_reserved":
                    quantity_reserved,

                "quantity_available":
                    quantity_available,

                "safety_stock":
                    safety_stock,

                "reorder_point":
                    reorder_point,

                "inventory_value":
                    inventory_value,

            }

        )

        snapshot_number += 1

    inventory_snapshot_df = (
        pd.DataFrame(records)
        .sort_values(["warehouse_id", "product_id"])
        .reset_index(drop=True)
    )

    return inventory_snapshot_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    from products import generate_products
    from suppliers import generate_suppliers
    from warehouses import generate_warehouses
    from assignment import generate_product_warehouse_assignment

    from utils import assign_demand_tiers

    suppliers_df = generate_suppliers()

    products_df = generate_products(
        suppliers_df=suppliers_df
    )

    warehouses_df = generate_warehouses()

    demand_tiers = assign_demand_tiers(products_df)

    assignment_df = generate_product_warehouse_assignment(
        products_df=products_df,
        warehouses_df=warehouses_df,
        demand_tiers=demand_tiers,
    )

    inventory_snapshot_df = generate_inventory_snapshot(
        products_df=products_df,
        warehouses_df=warehouses_df,
        assignment_df=assignment_df,
    )

    print(inventory_snapshot_df.head())
    print()
    print(inventory_snapshot_df.info())