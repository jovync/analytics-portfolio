"""
Customer Master Generator

Creates the enterprise customer dimension.

Customers are generated independently from transactions,
allowing downstream sales, marketing, CRM, and retention
analytics to reference a persistent customer master.
"""

import random

import pandas as pd
from faker import Faker

from config import START_DATE

fake = Faker()


COUNTRIES = [
    "Singapore",
    "Malaysia",
    "Thailand",
    "Philippines",
]

LOYALTY_TIERS = [
    ("Bronze", 0.55),
    ("Silver", 0.25),
    ("Gold", 0.15),
    ("Platinum", 0.05),
]

ACQUISITION_CHANNELS = [
    ("Organic Search", 0.30),
    ("Facebook Ads", 0.20),
    ("Instagram", 0.18),
    ("TikTok", 0.12),
    ("Referral", 0.10),
    ("Email Campaign", 0.10),
]

CUSTOMER_STATUS = [
    ("Active", 0.90),
    ("Inactive", 0.10),
]


def weighted_choice(options):
    """
    Helper for weighted random selections.

    Parameters
    ----------
    options : list[tuple]

    Returns
    -------
    Any
    """
    values = [x[0] for x in options]
    weights = [x[1] for x in options]
    return random.choices(values, weights=weights, k=1)[0]


def generate_customers(count: int, seed: int) -> pd.DataFrame:
    """
    Generate enterprise customer master.
    """

    Faker.seed(seed)
    random.seed(seed)

    customers = []

    for i in range(1, count + 1):

        signup_date = fake.date_between(
            start_date=START_DATE.date(),
            end_date="today",
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
                "customer_id": f"CUST-{i:06d}",

                "first_name": fake.first_name(),
                "last_name": fake.last_name(),

                "email": fake.unique.email(),

                "phone": fake.phone_number(),

                "country": random.choice(COUNTRIES),

                "gender": gender,

                "birth_date": birth_date,

                "customer_since": signup_date,

                "loyalty_tier": weighted_choice(LOYALTY_TIERS),

                "acquisition_channel": weighted_choice(
                    ACQUISITION_CHANNELS
                ),

                "customer_status": weighted_choice(
                    CUSTOMER_STATUS
                ),
            }
        )

    return pd.DataFrame(customers)


if __name__ == "__main__":

    df = generate_customers(
        count=10,
        seed=42,
    )

    print(df.head())