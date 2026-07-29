"""
Supplier Master Data Generator

Generates the enterprise supplier master used by
NetSuite Procurement and Purchasing.

Output:
    pandas.DataFrame
"""

from __future__ import annotations

import random
from datetime import timedelta

import pandas as pd

from config import (
    RANDOM_SEED,
    NUM_SUPPLIERS,
    SIMULATION_START_DATE,
    PRODUCT_CATALOG,
)

from utils import fake, weighted_choice, generate_id

# =============================================================================
# REFERENCE DATA
# =============================================================================

SUPPLIER_PREFIXES = [
    "Lotus",
    "Pacific",
    "Evergreen",
    "Nova",
    "Atlas",
    "Harmony",
    "Summit",
    "Prime",
    "Zenith",
    "EastBridge",
    "BlueWave",
    "Global",
    "Vertex",
    "Pioneer",
    "Golden",
    "Aurora",
]

SUPPLIER_SUFFIXES = [
    "Manufacturing",
    "Consumer Goods",
    "Industrial",
    "Supply Group",
    "Trading",
    "Beauty Labs",
    "Lifestyle Co.",
    "Textiles",
    "Packaging",
    "Components",
    "Holdings",
]

# Sourcing countries, weighted toward where SEA retail manufacturing
# actually concentrates (China dominant, Singapore mostly a trading/
# finance hub rather than a manufacturing origin).

COUNTRY_CURRENCY = {
    "China": "CNY",
    "Vietnam": "USD",
    "Thailand": "THB",
    "Malaysia": "MYR",
    "Singapore": "SGD",
    "Indonesia": "IDR",
}

COUNTRY_WEIGHTS = {
    "China": 0.45,
    "Vietnam": 0.20,
    "Thailand": 0.10,
    "Malaysia": 0.10,
    "Indonesia": 0.10,
    "Singapore": 0.05,
}

PAYMENT_TERMS = [
    "Net 30",
    "Net 45",
    "Net 60",
    "Net 90",
]

SUPPLIER_TIERS = {
    "Strategic": 0.15,
    "Preferred": 0.35,
    "Standard": 0.50,
}

# Category specialty: which part of the product catalog this
# supplier makes. Lets products.py assign suppliers that actually
# match the product's category instead of a fully random pick.
# Roughly even across the 4 categories at this supplier count
# (~30 / 4 suppliers per category).

CATEGORY_SPECIALTIES = {
    category: round(1 / len(PRODUCT_CATALOG), 4)
    for category in PRODUCT_CATALOG.keys()
}


# =============================================================================
# GENERATOR
# =============================================================================

def generate_suppliers(
    supplier_count: int = NUM_SUPPLIERS,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate enterprise supplier master.

    Parameters
    ----------
    supplier_count
        Number of suppliers to generate.

    seed
        Random seed for reproducible results.

    Returns
    -------
    pandas.DataFrame
    """

    random.seed(seed)
    fake.seed_instance(seed)

    suppliers = []

    existing_names = set()

    for supplier_number in range(1, supplier_count + 1):

        # ----------------------------------------------------------
        # Ensure supplier names are unique
        # ----------------------------------------------------------

        while True:

            supplier_name = (
                f"{random.choice(SUPPLIER_PREFIXES)} "
                f"{random.choice(SUPPLIER_SUFFIXES)}"
            )

            if supplier_name not in existing_names:
                existing_names.add(supplier_name)
                break

        # ----------------------------------------------------------
        # Country / Currency
        # ----------------------------------------------------------

        country = weighted_choice(COUNTRY_WEIGHTS)

        currency = COUNTRY_CURRENCY[country]

        # ----------------------------------------------------------
        # Category Specialty
        # ----------------------------------------------------------

        category_specialty = weighted_choice(CATEGORY_SPECIALTIES)

        # ----------------------------------------------------------
        # Supplier Tier
        # ----------------------------------------------------------

        supplier_tier = weighted_choice(SUPPLIER_TIERS)

        preferred_supplier = supplier_tier in (
            "Strategic",
            "Preferred",
        )

        # ----------------------------------------------------------
        # Lead Time
        # ----------------------------------------------------------

        if supplier_tier == "Strategic":
            lead_time = random.randint(10, 18)

        elif supplier_tier == "Preferred":
            lead_time = random.randint(18, 28)

        else:
            lead_time = random.randint(25, 45)

        # ----------------------------------------------------------
        # Quality Rating
        # ----------------------------------------------------------

        if supplier_tier == "Strategic":

            quality_rating = round(
                random.uniform(4.7, 5.0),
                2,
            )

        elif supplier_tier == "Preferred":

            quality_rating = round(
                random.uniform(4.2, 4.8),
                2,
            )

        else:

            quality_rating = round(
                random.uniform(3.5, 4.5),
                2,
            )

        # ----------------------------------------------------------
        # Supplier Created Date
        # ----------------------------------------------------------

        created_at = (
            SIMULATION_START_DATE
            - timedelta(days=random.randint(90, 1200))
        ).date()

        # ----------------------------------------------------------
        # Record
        # ----------------------------------------------------------

        suppliers.append(

            {

                "supplier_id":
                    generate_id("SUP", supplier_number, width=4),

                "supplier_name":
                    supplier_name,

                "supplier_tier":
                    supplier_tier,

                "category_specialty":
                    category_specialty,

                "country":
                    country,

                "currency":
                    currency,

                "payment_terms":
                    random.choice(PAYMENT_TERMS),

                "lead_time_days":
                    lead_time,

                "quality_rating":
                    quality_rating,

                "preferred_supplier":
                    preferred_supplier,

                "created_at":
                    created_at,

            }

        )

    suppliers_df = pd.DataFrame(suppliers)

    suppliers_df = (
        suppliers_df
        .sort_values("supplier_id")
        .reset_index(drop=True)
    )

    return suppliers_df