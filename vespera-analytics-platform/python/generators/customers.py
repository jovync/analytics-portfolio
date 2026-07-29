"""
Customer Master Generator

Creates the enterprise customer master used throughout
the Vespera Analytics Platform.

Customers are generated independently from transactions,
allowing Sales, CRM, Marketing, and Customer Analytics
to reference a persistent customer dimension.
"""

from __future__ import annotations

import random

import pandas as pd

from config import (
    NUM_CUSTOMERS,
    RANDOM_SEED,
    SIMULATION_START_DATE,
    SIMULATION_END_DATE,
    CUSTOMER_COUNTRIES,
)

from utils import get_faker, weighted_choice, generate_id

# =============================================================================
# REFERENCE DATA
# =============================================================================

LOYALTY_TIERS = {
    "Bronze": 0.55,
    "Silver": 0.25,
    "Gold": 0.15,
    "Platinum": 0.05,
}

ACQUISITION_CHANNELS = {
    "Organic Search": 0.30,
    "Facebook Ads": 0.20,
    "Instagram": 0.18,
    "TikTok": 0.12,
    "Referral": 0.10,
    "Email Campaign": 0.10,
}

CUSTOMER_STATUS = {
    "Active": 0.90,
    "Inactive": 0.10,
}


# =============================================================================
# GENERATOR
# =============================================================================

def generate_customers(
    customer_count: int = NUM_CUSTOMERS,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate enterprise customer master.
    """

    random.seed(seed)

    customers = []

    for customer_number in range(1, customer_count + 1):

        # ----------------------------------------------------------
        # Country (assigned first — drives locale for name/phone)
        # ----------------------------------------------------------

        country = weighted_choice(CUSTOMER_COUNTRIES)

        fake = get_faker(country)

        signup_date = fake.date_between(
            start_date=SIMULATION_START_DATE.date(),
            end_date=SIMULATION_END_DATE.date(),
        )

        birth_date = fake.date_of_birth(
            minimum_age=18,
            maximum_age=70,
        )

        gender = random.choice(
            [
                "Female",
                "Male",
            ]
        )

        customers.append(

            {

                "customer_id":
                    generate_id("CUST", customer_number, width=6),

                "first_name":
                    fake.first_name(),

                "last_name":
                    fake.last_name(),

                "email":
                    fake.unique.email(),

                "phone":
                    fake.phone_number(),

                "country":
                    country,

                "gender":
                    gender,

                "birth_date":
                    birth_date,

                "customer_since":
                    signup_date,

                "loyalty_tier":
                    weighted_choice(LOYALTY_TIERS),

                "acquisition_channel":
                    weighted_choice(ACQUISITION_CHANNELS),

                "customer_status":
                    weighted_choice(CUSTOMER_STATUS),

            }

        )

    customers_df = (
        pd.DataFrame(customers)
        .sort_values("customer_id")
        .reset_index(drop=True)
    )

    return customers_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    customers_df = generate_customers()

    print(customers_df.head())
    print()
    print(customers_df["country"].value_counts())
    print()
    print(customers_df.info())