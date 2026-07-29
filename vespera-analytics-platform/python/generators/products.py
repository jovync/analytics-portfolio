"""
Enterprise Product Master Generator

Creates the enterprise product catalog used throughout the
Synthetic Enterprise Simulation Engine.

This dataset represents the ERP Item Master (NetSuite) and is
referenced by Sales, Procurement, Inventory, Manufacturing,
Logistics, and Finance.
"""

from __future__ import annotations

import random

import numpy as np
import pandas as pd

from config import (
    BRANDS,
    NUM_PRODUCTS,
    PRODUCT_CATALOG,
    RANDOM_SEED,
    SIMULATION_START_DATE,
    SIMULATION_END_DATE,
)

from utils import weighted_choice, generate_id

# New-launch window: products launched within this many days of
# SIMULATION_END_DATE are always "New Launch" rather than randomly
# assigned, so lifecycle_status stays consistent with launch_date.

NEW_LAUNCH_WINDOW_DAYS = 60

LIFECYCLE_WEIGHTS = {
    "Active": 0.85,
    "Discontinued": 0.15,
}


# =============================================================================
# GENERATOR
# =============================================================================

def generate_products(
    product_count: int = NUM_PRODUCTS,
    suppliers_df: pd.DataFrame | None = None,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate the enterprise product master.

    Parameters
    ----------
    product_count
        Number of products to generate.

    suppliers_df
        Supplier master data. Must include a `category_specialty`
        column so products can be assigned a supplier that actually
        makes that category.

    seed
        Random seed for reproducible results.

    Returns
    -------
    pandas.DataFrame
    """

    if suppliers_df is None:
        raise ValueError(
            "suppliers_df is required to generate products."
        )

    random.seed(seed)
    np.random.seed(seed)

    categories = list(PRODUCT_CATALOG.keys())

    # Pre-split supplier pool by category specialty so each product
    # draws only from suppliers who actually make that category.

    suppliers_by_category = {
        category: suppliers_df.loc[
            suppliers_df["category_specialty"] == category,
            "supplier_id",
        ].tolist()
        for category in categories
    }

    all_supplier_ids = suppliers_df["supplier_id"].tolist()

    products = []

    existing_names = set()

    for product_number in range(1, product_count + 1):

        # ----------------------------------------------------------
        # Category
        # ----------------------------------------------------------

        category = random.choice(categories)

        cfg = PRODUCT_CATALOG[category]

        # ----------------------------------------------------------
        # Product Naming (unique, with variant to avoid collisions)
        # ----------------------------------------------------------

        while True:

            brand = random.choice(BRANDS)

            adjective = random.choice(cfg["adjectives"])

            product = random.choice(cfg["products"])

            variant = random.choice(cfg["variants"])

            product_name = (
                f"{brand} {adjective} {product} - {variant}"
            )

            if product_name not in existing_names:
                existing_names.add(product_name)
                break

        # ----------------------------------------------------------
        # Supplier (category-aware; falls back to any supplier if
        # a category somehow has no specialists assigned)
        # ----------------------------------------------------------

        candidate_suppliers = (
            suppliers_by_category[category] or all_supplier_ids
        )

        supplier_id = random.choice(candidate_suppliers)

        # ----------------------------------------------------------
        # Pricing
        # ----------------------------------------------------------

        base_cost = round(
            random.uniform(
                cfg["base_cost"][0],
                cfg["base_cost"][1],
            ),
            2,
        )

        markup = random.uniform(*cfg["markup"])

        msrp = round(base_cost * markup, 2)

        # ----------------------------------------------------------
        # Product Lifecycle
        # ----------------------------------------------------------

        # 85% of products already existed before the simulation starts
        # (a real retailer has an established catalog on day one).
        # The remaining 15% are genuine new launches introduced during
        # the simulation window, which is what New Launch / seasonal
        # ramp-up should actually represent.

        if random.random() < 0.85:

            launch_date = (
                SIMULATION_START_DATE
                - pd.Timedelta(days=random.randint(30, 900))
            )

        else:

            launch_date = (
                SIMULATION_START_DATE
                + pd.Timedelta(days=random.randint(1, 730))
            )

        days_to_sim_end = (SIMULATION_END_DATE - launch_date).days

        discontinued_date = None

        if days_to_sim_end <= NEW_LAUNCH_WINDOW_DAYS:

            # Launched too recently to have accumulated a track
            # record yet — cannot be "Discontinued" this soon.
            lifecycle_status = "New Launch"

        else:

            lifecycle_status = weighted_choice(LIFECYCLE_WEIGHTS)

            if lifecycle_status == "Discontinued":

                discontinued_date = (
                    launch_date
                    + pd.Timedelta(
                        days=random.randint(
                            30,
                            max(31, days_to_sim_end - 1),
                        )
                    )
                ).date()

        # ----------------------------------------------------------
        # Demand Characteristics
        # ----------------------------------------------------------

        popularity_weight = round(
            float(np.random.pareto(1.5) + 0.1),
            4,
        )

        # ----------------------------------------------------------
        # Inventory Planning
        # ----------------------------------------------------------

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

        # ----------------------------------------------------------
        # Record
        # ----------------------------------------------------------

        products.append(

            {

                "product_id":
                    generate_id("PRD", product_number, width=5),

                "sku":
                    generate_id("SKU", product_number, width=5),

                "product_name":
                    product_name,

                "category":
                    category,

                "brand":
                    brand,

                "supplier_id":
                    supplier_id,

                "base_cost_sgd":
                    base_cost,

                "msrp_sgd":
                    msrp,

                "launch_date":
                    launch_date.date(),

                "lifecycle_status":
                    lifecycle_status,

                "discontinued_date":
                    discontinued_date,

                "popularity_weight":
                    popularity_weight,

                "return_rate":
                    cfg["return_rate"],

                "reorder_point":
                    reorder_point,

                "reorder_quantity":
                    reorder_quantity,

                "lead_time_days":
                    lead_time_days,

            }

        )

    products_df = (
        pd.DataFrame(products)
        .sort_values("product_id")
        .reset_index(drop=True)
    )

    return products_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    from suppliers import generate_suppliers

    suppliers_df = generate_suppliers()

    products_df = generate_products(
        suppliers_df=suppliers_df
    )

    print(products_df.head())
    print()
    print(products_df["category"].value_counts())
    print()
    print(products_df["lifecycle_status"].value_counts())
    print()
    print(products_df.info())