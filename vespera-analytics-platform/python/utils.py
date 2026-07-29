"""
Shared utility functions used across the simulation engine.

Every generator should import weighted_choice, generate_id, money,
get_faker, and assign_demand_tiers from here rather than
reimplementing them locally.
"""

import random

import numpy as np
import pandas as pd

from faker import Faker

from config import RANDOM_SEED, FAKER_LOCALES

# ---------------------------------------------------------------------
# GLOBAL RANDOM STATE
# ---------------------------------------------------------------------
# Note: individual generator functions also accept a `seed` parameter
# and reseed internally. That's intentional — it keeps each generator
# independently reproducible regardless of call order, rather than
# relying on execution order after a single import-time seed here.
# ---------------------------------------------------------------------

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
Faker.seed(RANDOM_SEED)

fake = Faker()

_locale_faker_cache = {}


def get_faker(country: str) -> Faker:
    """
    Return a Faker instance localized to the given country.

    Uses a fallback chain [country_locale, "en_US"] rather than a
    single locale, since some locale providers don't implement
    every method (e.g. phone_number()) and would otherwise raise
    AttributeError.

    Falls back entirely to the default `fake` instance if no locale
    mapping exists for the country, or if the configured locale
    fails to initialize at all (e.g. an invalid/unsupported locale
    code in this Faker install).
    """

    if country not in FAKER_LOCALES:
        return fake

    if country not in _locale_faker_cache:
        try:
            locale_faker = Faker([FAKER_LOCALES[country], "en_US"])
            locale_faker.seed_instance(RANDOM_SEED)
            _locale_faker_cache[country] = locale_faker
        except AttributeError:
            # Locale isn't valid/available in this Faker install —
            # fall back to the default instance rather than crashing
            # the whole generation run over one bad locale code.
            _locale_faker_cache[country] = fake

    return _locale_faker_cache[country]


def weighted_choice(options: dict):
    """
    Select one item from a dictionary of probabilities.

    Example
    -------
    weighted_choice({"Shopify": 0.4, "Shopee": 0.3, "Lazada": 0.3})
    """

    values = list(options.keys())
    weights = list(options.values())

    assert abs(sum(weights) - 1.0) < 1e-6, (
        f"Weights must sum to 1.0, got {sum(weights)}"
    )

    return random.choices(
        values,
        weights=weights,
        k=1,
    )[0]


def generate_id(prefix: str, number: int, width: int = 6) -> str:
    """
    Standard ID format across all entities.

    Example
    -------
    generate_id("CUST", 42) -> "CUST-000042"
    """

    return f"{prefix}-{str(number).zfill(width)}"


def pareto_weights(n: int, alpha: float = 1.16) -> list:
    """
    Generate n normalized weights following an approximate 80/20
    distribution. Lower alpha = more extreme skew.
    """

    raw = np.random.pareto(alpha, n) + 1

    return (raw / raw.sum()).tolist()


def money(value: float) -> float:
    """
    Standard currency rounding.
    """

    return round(float(value), 2)


def assign_demand_tiers(products_df: pd.DataFrame) -> pd.Series:
    """
    Buckets products into quartiles by popularity_weight percentile
    rank: Low / Medium / High / Very High. Percentile rank is used
    instead of raw popularity_weight because that value is
    Pareto-distributed with a long tail, making raw values
    incomparable across products.

    Returned Series is index-aligned with products_df, so callers
    should look up a product's tier via demand_tiers.loc[idx] using
    the same index products_df was iterated with.

    Shared across assignment.py and purchase_orders.py (and
    generate_data.py, which computes it once and passes it to both)
    so every generator agrees on the same tier for the same product.
    """

    percentile_rank = products_df["popularity_weight"].rank(pct=True)

    tiers = pd.cut(
        percentile_rank,
        bins=[0, 0.50, 0.80, 0.95, 1.0],
        labels=["Low", "Medium", "High", "Very High"],
        include_lowest=True,
    )

    return tiers