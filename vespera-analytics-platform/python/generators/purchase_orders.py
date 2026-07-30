"""
Purchase Order Generator

Creates enterprise purchase order records representing
inbound stock replenishment from suppliers to warehouses.

This is the supply-side counterpart to Customer Sales in the
inventory ledger. Without it, warehouses only ever lose stock
(via sales) and never meaningfully gain it (returns alone cover
~4-8% of sales volume), so on-hand quantity would trend toward
negative for any popular product.

Which (warehouse, product) pairs actually get purchase orders is
now driven entirely by assignment_df (generated once in
assignment.py) instead of this file rolling its own independent
stocking probability. This guarantees a warehouse only ever
receives POs for products it's actually assigned to carry — the
same table inventory_snapshot.py and order_items.py use — so all
three can never disagree with each other about what a warehouse
stocks.

Order quantity and reorder cycle both scale by each product's
demand_tier (Low/Medium/High/Very High, based on popularity_weight
percentile rank — see utils.assign_demand_tiers), so high-demand
SKUs are ordered in bigger batches, more often.

Each record represents one purchase order line: one product,
from one supplier, replenishing one warehouse.
"""

from __future__ import annotations

import random

import pandas as pd

from config import (
    RANDOM_SEED,
    SIMULATION_START_DATE,
    SIMULATION_END_DATE,
)

from utils import generate_id

# =============================================================================
# CONFIGURATION
# =============================================================================

REORDER_CYCLE_DAYS = {

    "Distribution Center": (28, 42),

    "Retail Store": (18, 30),

}

STORE_ORDER_QUANTITY_RANGE = (80, 200)

UNIT_COST_VARIANCE = (0.95, 1.08)

LATE_RECEIPT_PROBABILITY = 0.12
LATE_RECEIPT_EXTRA_DAYS = (2, 10)

# ----------------------------------------------------------------
# Demand-tier scaling
# ----------------------------------------------------------------
# popularity_weight is Pareto-distributed, so a small number of
# products drive a disproportionate share of sales (by design —
# see products.py). Flat replenishment quantity/cadence can't keep
# pace with those SKUs. Order quantity is multiplied up and cycle
# length divided down per tier, so hot SKUs are ordered in bigger
# batches, more often.
# ----------------------------------------------------------------

DEMAND_TIER_QUANTITY_MULTIPLIER = {

    "Low": 1.0,

    "Medium": 1.6,

    "High": 2.5,

    "Very High": 4.5,

}

DEMAND_TIER_CYCLE_DIVISOR = {

    "Low": 1.0,

    "Medium": 1.3,

    "High": 1.8,

    "Very High": 2.5,

}

MIN_CYCLE_DAYS = 7


# =============================================================================
# GENERATOR
# =============================================================================

def generate_purchase_orders(
    products_df: pd.DataFrame,
    suppliers_df: pd.DataFrame,
    warehouses_df: pd.DataFrame,
    assignment_df: pd.DataFrame,
    demand_tiers: pd.Series,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate enterprise purchase orders.

    Parameters
    ----------
    products_df
        Product master.

    suppliers_df
        Supplier master.

    warehouses_df
        Warehouse master.

    assignment_df
        Output of assignment.generate_product_warehouse_assignment().
        Defines exactly which (warehouse_id, product_id) pairs are
        eligible to receive purchase orders — anything not in this
        table gets none.

    demand_tiers
        Output of utils.assign_demand_tiers(products_df). Index-
        aligned with products_df; used to scale order quantity and
        cycle length per product.

    seed
        Random seed for reproducible results.

    Returns
    -------
    pandas.DataFrame
    """

    random.seed(seed)

    supplier_lookup = suppliers_df.set_index("supplier_id")[
        ["lead_time_days", "currency"]
    ].to_dict(orient="index")

    warehouse_type_lookup = warehouses_df.set_index(
        "warehouse_id"
    )["warehouse_type"].to_dict()

    # product_id -> list of warehouse_ids assigned to carry it
    assigned_warehouses_by_product = (
        assignment_df.groupby("product_id")["warehouse_id"]
        .apply(list)
        .to_dict()
    )

    records = []

    po_number = 1

    for idx, product in products_df.iterrows():

        product_id = product["product_id"]
        supplier_id = product["supplier_id"]
        base_cost = product["base_cost_sgd"]
        reorder_quantity = product["reorder_quantity"]

        demand_tier = demand_tiers.loc[idx]

        quantity_multiplier = DEMAND_TIER_QUANTITY_MULTIPLIER[demand_tier]

        cycle_divisor = DEMAND_TIER_CYCLE_DIVISOR[demand_tier]

        supplier_info = supplier_lookup.get(supplier_id)

        if supplier_info is None:
            # Shouldn't happen given products.py always assigns a
            # valid supplier_id, but avoids a hard crash if data
            # drifts out of sync.
            continue

        supplier_lead_time = supplier_info["lead_time_days"]

        launch_date = pd.Timestamp(product["launch_date"])
        discontinued_date = product["discontinued_date"]

        effective_start = max(
            launch_date,
            pd.Timestamp(SIMULATION_START_DATE),
        )

        effective_end = pd.Timestamp(SIMULATION_END_DATE)

        if pd.notna(discontinued_date):
            effective_end = min(
                effective_end,
                pd.Timestamp(discontinued_date),
            )

        if effective_start >= effective_end:
            # Product has no active window to be replenished in.
            continue

        assigned_warehouse_ids = assigned_warehouses_by_product.get(
            product_id, []
        )

        for warehouse_id in assigned_warehouse_ids:

            warehouse_type = warehouse_type_lookup[warehouse_id]

            cycle_min, cycle_max = REORDER_CYCLE_DAYS[warehouse_type]

            # ----------------------------------------------------------
            # First PO for this (warehouse, product) should land stock
            # at or just before the product's own launch/assignment
            # start, so it has opening availability rather than a
            # stockout on day one.
            # ----------------------------------------------------------

            first_order_offset = random.randint(0, 5)

            order_date = effective_start + pd.Timedelta(
                days=first_order_offset
            )

            while order_date <= effective_end:

                is_late = random.random() < LATE_RECEIPT_PROBABILITY

                lead_time = supplier_lead_time

                if is_late:
                    lead_time += random.randint(
                        *LATE_RECEIPT_EXTRA_DAYS
                    )

                expected_receipt_date = order_date + pd.Timedelta(
                    days=supplier_lead_time
                )

                actual_receipt_date = order_date + pd.Timedelta(
                    days=lead_time
                )

                if actual_receipt_date > pd.Timestamp(
                    SIMULATION_END_DATE
                ):
                    po_status = "In Transit"
                    actual_receipt_date = pd.NaT
                else:
                    po_status = "Received"

                # ----------------------------------------------------------
                # Quantity: scaled by demand tier
                # ----------------------------------------------------------

                if warehouse_type == "Distribution Center":
                    # reorder_quantity is now already demand-scaled
                    # (see products.py) — applying quantity_multiplier
                    # on top would double-count demand tier.
                    base_quantity = reorder_quantity
                    quantity_ordered = base_quantity
                else:
                    base_quantity = random.randint(
                        *STORE_ORDER_QUANTITY_RANGE
                    )
                    quantity_ordered = int(
                        round(base_quantity * quantity_multiplier)
                    )

                unit_cost = round(
                    base_cost * random.uniform(*UNIT_COST_VARIANCE),
                    2,
                )

                total_cost = round(
                    quantity_ordered * unit_cost,
                    2,
                )

                records.append(

                    {

                        "purchase_order_id":
                            generate_id("PO", po_number, width=8),

                        "supplier_id":
                            supplier_id,

                        "product_id":
                            product_id,

                        "warehouse_id":
                            warehouse_id,

                        "order_date":
                            order_date,

                        "expected_receipt_date":
                            expected_receipt_date,

                        "actual_receipt_date":
                            actual_receipt_date,

                        "quantity_ordered":
                            quantity_ordered,

                        "quantity_received":
                            quantity_ordered
                            if po_status == "Received"
                            else 0,

                        "unit_cost_sgd":
                            unit_cost,

                        "total_cost_sgd":
                            total_cost,

                        "po_status":
                            po_status,

                        "demand_tier":
                            demand_tier,

                    }

                )

                po_number += 1

                # ----------------------------------------------------------
                # Cycle length: shortened by demand tier, so hot
                # products get reordered more frequently.
                # ----------------------------------------------------------

                base_cycle = random.randint(cycle_min, cycle_max)

                cycle_length = max(
                    MIN_CYCLE_DAYS,
                    int(round(base_cycle / cycle_divisor)),
                )

                order_date = order_date + pd.Timedelta(
                    days=cycle_length
                )

    purchase_orders_df = (
        pd.DataFrame(records)
        .sort_values(["order_date", "purchase_order_id"])
        .reset_index(drop=True)
    )

    return purchase_orders_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    from suppliers import generate_suppliers
    from products import generate_products
    from warehouses import generate_warehouses
    from assignment import generate_product_warehouse_assignment

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

    purchase_orders_df = generate_purchase_orders(
        products_df=products_df,
        suppliers_df=suppliers_df,
        warehouses_df=warehouses_df,
        assignment_df=assignment_df,
        demand_tiers=demand_tiers,
    )

    print(purchase_orders_df.head())
    print()
    print(purchase_orders_df["po_status"].value_counts())
    print()
    print(purchase_orders_df["demand_tier"].value_counts())
    print()
    print(purchase_orders_df.info())