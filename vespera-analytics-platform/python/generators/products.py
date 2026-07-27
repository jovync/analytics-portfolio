"""
Enterprise Product Master Generator

Creates the enterprise product catalog used throughout the
Synthetic Enterprise Simulation Engine.

This dataset represents the ERP Item Master (NetSuite) and is
referenced by Sales, Procurement, Inventory, Manufacturing,
and Finance.
"""

import random

import numpy as np
import pandas as pd

from ..config import (
    BRANDS,
    PRODUCT_NAME_PATTERNS,
    START_DATE,
)


def generate_products(
    count: int,
    suppliers_df: pd.DataFrame,
    seed: int,
) -> pd.DataFrame:
    """
    Generate the enterprise product master.

    Parameters
    ----------
    count : int
        Number of products.

    suppliers_df : pd.DataFrame
        Supplier master.

    seed : int
        Random seed.

    Returns
    -------
    pd.DataFrame
    """

    random.seed(seed)
    np.random.seed(seed)

    supplier_ids = suppliers_df["supplier_id"].tolist()

    categories = list(PRODUCT_NAME_PATTERNS.keys())

    products = []

    for i in range(1, count + 1):

        category = random.choice(categories)

        cfg = PRODUCT_NAME_PATTERNS[category]

        adjective = random.choice(cfg["adjectives"])
        noun = random.choice(cfg["nouns"])

        brand = random.choice(BRANDS)

        product_name = f"{brand} {adjective} {noun}"

        supplier_id = random.choice(supplier_ids)

        base_cost = round(
            random.uniform(
                cfg["base_cost_range"][0],
                cfg["base_cost_range"][1],
            ),
            2,
        )

        msrp = round(
            base_cost * cfg["markup"],
            2,
        )

        launch_date = pd.Timestamp(
            random.choice(
                pd.date_range(
                    START_DATE,
                    periods=900,
                    freq="D",
                )
            )
        )

        lifecycle_status = random.choices(
            [
                "Active",
                "New Launch",
                "Discontinued",
            ],
            weights=[
                0.80,
                0.10,
                0.10,
            ],
        )[0]

        popularity_weight = float(
            np.random.pareto(1.5) + 0.1
        )

        reorder_point = random.choice(
            [
                50,
                100,
                150,
                200,
            ]
        )

        reorder_quantity = random.choice(
            [
                250,
                500,
                1000,
            ]
        )

        lead_time_days = random.randint(
            10,
            35,
        )

        products.append(
            {
                "product_id": i,

                "sku": f"SKU-{i:05d}",

                "product_name": product_name,

                "category": category,

                "brand": brand,

                "supplier_id": supplier_id,

                "base_cost_sgd": base_cost,

                "msrp_sgd": msrp,

                "launch_date": launch_date.date(),

                "lifecycle_status": lifecycle_status,

                "popularity_weight": round(
                    popularity_weight,
                    4,
                ),

                "return_rate": cfg["return_rate"],

                "reorder_point": reorder_point,

                "reorder_quantity": reorder_quantity,

                "lead_time_days": lead_time_days,
            }
        )

    df = pd.DataFrame(products)

    return df


if __name__ == "__main__":

    from generators.suppliers import generate_suppliers
    from config import (
        TARGET_ITEMS,
        TARGET_SUPPLIERS,
        SEED,
    )

    suppliers = generate_suppliers(
        TARGET_SUPPLIERS,
        SEED,
    )

    df = generate_products(
        TARGET_ITEMS,
        suppliers,
        SEED,
    )

    print(df.head())
    print()
    print(df["category"].value_counts())