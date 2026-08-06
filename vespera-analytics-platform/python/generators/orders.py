"""
Order Header Generator

Creates enterprise customer order headers for the
Vespera Analytics Platform.

Each record represents one customer order.

Order line items are generated separately by
order_items.py.

BUGFIX (v1.2, caught during Looker Studio dashboard validation):
order_date is now constrained to fall on or after each sampled
customer's customer_since (signup date). The original version
sampled customer and order_date as two fully independent arrays with
no relationship between them, so a customer could be assigned an
order date years before they signed up. Verified against the live
data: ~47% of all order line items (44,635 of 94,127) had
order_date < customer_since before this fix -- not an edge case, a
majority-affecting chronological impossibility. This silently broke
any tenure/cohort-based analysis downstream (e.g. LTV by signup
cohort showed no cohort-curve decline for recent signups, since
order dates were effectively decoupled from actual customer tenure).
Aggregate totals (total order count, total revenue) are NOT affected
by this fix -- only WHICH dates orders land on shifts, so anything
built on point-in-time or cumulative totals should be unaffected;
anything built on customer tenure/cohort timing will change.
"""

from __future__ import annotations

import bisect
import random

import numpy as np
import pandas as pd

from config import (
    CHANNELS,
    ORDER_STATUS,
    PAYMENT_METHODS,
    RANDOM_SEED,
    SIMULATION_START_DATE,
    SIMULATION_END_DATE,
    TARGET_ORDER_COUNT,
    SEASONALITY_MULTIPLIERS,
    LOYALTY_ORDER_FREQUENCY_WEIGHTS,
)

from utils import weighted_choice, generate_id

# Channel -> warehouse type it's allowed to fulfill from.
# Retail (walk-in) orders can only be fulfilled by a physical store
# in the customer's own country. Online channels fulfill from
# whichever warehouse (DC or store) serves that customer's country.

RETAIL_CHANNEL = "Retail"


# =============================================================================
# HELPERS
# =============================================================================

def _build_month_weights() -> tuple:
    """
    Expand SEASONALITY_MULTIPLIERS into per-day weights across the
    simulation window, so random date sampling can respect monthly
    seasonality instead of being flat.

    Returns a plain list of Timestamps (not a DatetimeIndex) and a
    numpy array of weights, so per-customer slicing in the main loop
    below (constraining to dates >= customer_since) is cheap --
    slicing a DatetimeIndex repeatedly inside a 50,000-iteration loop
    would be noticeably slower than slicing a plain list + ndarray.
    """

    date_range = pd.date_range(
        SIMULATION_START_DATE,
        SIMULATION_END_DATE,
        freq="D",
    )

    weights = np.array([
        SEASONALITY_MULTIPLIERS[d.month]
        for d in date_range
    ])

    return list(date_range), weights


def _build_fulfillment_lookup(warehouses_df: pd.DataFrame) -> dict:
    """
    Build a lookup of {(country, channel_type): [warehouse_ids]}
    so fulfillment assignment respects geography and channel
    instead of picking any warehouse at random.

    channel_type is either "retail" (must be a physical store in
    the customer's own country) or "online" (any warehouse whose
    serves_countries includes the customer's country).
    """

    fulfillable = warehouses_df[
        warehouses_df["warehouse_type"] != "Returns Center"
    ]

    lookup = {}

    for _, warehouse in fulfillable.iterrows():

        for country in warehouse["serves_countries"]:

            # Online: any warehouse serving this country
            lookup.setdefault((country, "online"), []).append(
                warehouse["warehouse_id"]
            )

            # Retail: only stores physically located in that country
            if (
                warehouse["warehouse_type"] == "Retail Store"
                and warehouse["country"] == country
            ):
                lookup.setdefault((country, "retail"), []).append(
                    warehouse["warehouse_id"]
                )

    return lookup


def _assign_fulfillment_warehouse(
    country: str,
    channel: str,
    fulfillment_lookup: dict,
    fallback_warehouse_ids: list,
) -> str:
    """
    Pick a fulfillment warehouse for an order based on customer
    country and sales channel. Falls back to any warehouse if no
    match exists (shouldn't happen given current config, but avoids
    a hard crash if countries/warehouses drift out of sync later).
    """

    channel_type = "retail" if channel == RETAIL_CHANNEL else "online"

    candidates = fulfillment_lookup.get((country, channel_type))

    if not candidates and channel_type == "retail":
        # No local store for this country/channel combo — fall back
        # to online-eligible warehouses serving that country instead
        # of crashing (e.g. if Retail channel gets sampled for a
        # customer in a DC-only country).
        candidates = fulfillment_lookup.get((country, "online"))

    if not candidates:
        candidates = fallback_warehouse_ids

    return random.choice(candidates)


# =============================================================================
# GENERATOR
# =============================================================================

def generate_orders(
    customers_df: pd.DataFrame,
    warehouses_df: pd.DataFrame,
    order_count: int = TARGET_ORDER_COUNT,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate enterprise order headers.

    Each order's date is constrained to fall on or after that
    order's customer's customer_since — see module docstring for the
    bug this fixes.
    """

    random.seed(seed)

    fulfillment_lookup = _build_fulfillment_lookup(warehouses_df)

    all_warehouse_ids = warehouses_df.loc[
        warehouses_df["warehouse_type"] != "Returns Center",
        "warehouse_id",
    ].tolist()

    # ----------------------------------------------------------
    # Customer sampling weighted by loyalty tier, so higher-tier
    # customers generate a disproportionate share of orders
    # instead of every customer being equally likely.
    # ----------------------------------------------------------

    customer_ids = customers_df["customer_id"].tolist()
    customer_countries = customers_df["country"].tolist()

    # Assumed column name — matches how dim_customer.sql and
    # stg_customers already reference customer_since. If your actual
    # customers.py uses a different column name for signup date,
    # update this line to match before running.
    customer_since_dates = pd.to_datetime(
        customers_df["customer_since"]
    ).tolist()

    customer_weights = customers_df["loyalty_tier"].map(
        LOYALTY_ORDER_FREQUENCY_WEIGHTS
    ).tolist()

    customer_indices = list(range(len(customer_ids)))

    # ----------------------------------------------------------
    # Seasonality-weighted date sampling
    # ----------------------------------------------------------

    date_list, date_weights = _build_month_weights()

    records = []

    sampled_indices = random.choices(
        customer_indices,
        weights=customer_weights,
        k=order_count,
    )

    for order_number in range(1, order_count + 1):

        customer_idx = sampled_indices[order_number - 1]

        customer_id = customer_ids[customer_idx]
        customer_country = customer_countries[customer_idx]
        customer_since = customer_since_dates[customer_idx]

        # Constrain sampling to dates on/after this customer's
        # signup. bisect_left finds the first index in date_list
        # (sorted ascending, since it's built from pd.date_range)
        # that is >= customer_since, then we weighted-sample only
        # from that point forward. Every customer has at least one
        # valid day — their own signup date falls within the
        # simulation window by construction — so this slice is
        # never empty. Falls back to the full range defensively if
        # customer_since is somehow missing or out of bounds.
        if pd.isna(customer_since):
            valid_start = 0
        else:
            valid_start = bisect.bisect_left(date_list, customer_since)
            if valid_start >= len(date_list):
                valid_start = 0

        sampled_date = random.choices(
            date_list[valid_start:],
            weights=date_weights[valid_start:],
            k=1,
        )[0]

        order_date = (
            sampled_date
            + pd.Timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
        )

        status = weighted_choice(ORDER_STATUS)

        payment_method = weighted_choice(PAYMENT_METHODS)

        sales_channel = weighted_choice(CHANNELS)

        fulfillment_warehouse_id = _assign_fulfillment_warehouse(
            country=customer_country,
            channel=sales_channel,
            fulfillment_lookup=fulfillment_lookup,
            fallback_warehouse_ids=all_warehouse_ids,
        )

        records.append(

            {

                "order_id":
                    generate_id("ORD", order_number, width=8),

                "customer_id":
                    customer_id,

                "order_date":
                    order_date,

                "sales_channel":
                    sales_channel,

                "payment_method":
                    payment_method,

                "order_status":
                    status,

                "fulfillment_warehouse_id":
                    fulfillment_warehouse_id,

            }

        )

    orders_df = (
        pd.DataFrame(records)
        .sort_values("order_date")
        .reset_index(drop=True)
    )

    return orders_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    from customers import generate_customers
    from warehouses import generate_warehouses

    customers_df = generate_customers()

    warehouses_df = generate_warehouses()

    orders_df = generate_orders(
        customers_df=customers_df,
        warehouses_df=warehouses_df,
    )

    print(orders_df.head())
    print()
    print(orders_df["order_date"].dt.month.value_counts().sort_index())
    print()
    print(orders_df.info())

    # Sanity check for the bug this fix addresses — should print 0.
    merged = orders_df.merge(customers_df[["customer_id", "customer_since"]], on="customer_id")
    orders_before_signup = (
        pd.to_datetime(merged["order_date"]).dt.date
        < pd.to_datetime(merged["customer_since"]).dt.date
    ).sum()
    print()
    print(f"Orders before signup (should be 0): {orders_before_signup}")