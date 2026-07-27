"""
Shared utility functions used across the simulation engine.
"""

import random
import numpy as np

from faker import Faker

from config import RANDOM_SEED

# ---------------------------------------------------------------------
# GLOBAL RANDOM STATE
# ---------------------------------------------------------------------

fake = Faker()

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
Faker.seed(RANDOM_SEED)


def weighted_choice(options: dict):
    """
    Select one item from a dictionary of probabilities.

    Example

    {
        "Shopify": 0.4,
        "Shopee": 0.3
    }
    """

    values = list(options.keys())
    weights = list(options.values())

    return random.choices(
        values,
        weights=weights,
        k=1
    )[0]


def money(value: float) -> float:
    """
    Standard currency rounding.
    """

    return round(float(value), 2)