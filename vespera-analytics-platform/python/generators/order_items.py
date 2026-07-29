"""
Order Line Item Generator

Creates enterprise order line items for the
Vespera Analytics Platform.

Each record represents one product purchased
within an order.

Products offered in each order's basket are restricted to:
  1. Products actually launched and not yet discontinued as of
     the order's date.
  2. Products the fulfilling warehouse is actually assigned to
     carry (per assignment_df).

tax_amount is based on the fulfilling warehouse's country (point-
of-sale tax jurisdiction), and commission_amount is based on the
order's sales channel (marketplace channels like Shopee/Lazada
charge a seller commission; Shopify/Retail do not) — per the
Enterprise KPI Framework's Net Revenue formula, which requires
taxes and commissions at the line-item grain.
"""

from __future__ import annotations

import random
from datetime import date

import numpy as np
import pandas as pd

from config import (
    RANDOM_SEED,
    TAX_RATES_BY_COUNTRY,
    MARKETPLACE_COMMISSION_RATES,
)

from utils import weighted_choice, generate_id


# =============================================================================
# CONFIGURATION
# =============================================================================

BASKET_SIZE = {

    1: 0.50,

    2: 0.25,

    3: 0.15,

    4: 0.07,

    5: 0.03,

}

QUANTITY_WEIGHTS = {

    1: 0.55,

    2: 0.25,

    3: 0.12,

    4: 0.05,

    5: 0.02,

    6: 0.01,

}

DISCOUNT_WEIGHTS = {

    0.00: 0.65,

    0.05: 0.15,

    0.10: 0.12,

    0.15: 0.05,

    0.20: 0.03,

}

FAR_FUTURE_DATE = date(9999, 12, 31)


# =============================================================================
# HELPERS
# =============================================================================

def _weighted_sample_without_replacement(
    df: pd.DataFrame,
    n: int,
    weight_col: str,
) -> pd.DataFrame:
    """
    Weighted sampling without replacement via numpy instead of
    pandas.DataFrame.sample(weights=...). Pareto-distributed
    popularity_weight can produce a single item whose weight
    dominates the rest, which pandas' sampling algorithm rejects
    outright. numpy.random.choice has no such restriction.
    """

    weights = df[weight_col].to_numpy(dtype=float)
    weights = weights / weights.sum()

    chosen_positions = np.random.choice(
        len(df),
        size=n,
        replace=False,
        p=weights,
    )

    return df.iloc[chosen_positions]


# =============================================================================
# GENERATOR
# =============================================================================

def generate_order_items(
    orders_df: pd.DataFrame,
    products_df: pd.DataFrame,
    assignment_df: pd.DataFrame,
    warehouses_df: pd.DataFrame,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate enterprise order line items.

    Parameters
    ----------
    orders_df
        Order headers.

    products_df
        Product master.

    assignment_df
        Output of assignment.generate_product_warehouse_assignment().
        Restricts each order's basket to only products the
        fulfilling warehouse actually carries.

    warehouses_df
        Warehouse master. Used to look up the fulfilling
        warehouse's country for tax_amount calculation.

    seed
        Random seed for reproducible results.

    Returns
    -------
    pandas.DataFrame
    """

    random.seed(seed)
    np.random.seed(seed)

    records = []

    order_item_number = 1

    launch_dates = products_df["launch_date"].values

    discontinued_dates = (
        products_df["discontinued_date"]
        .fillna(FAR_FUTURE_DATE)
        .values
    )

    products_by_warehouse = (
        assignment_df.groupby("warehouse_id")["product_id"]
        .apply(set)
        .to_dict()
    )

    warehouse_country_lookup = warehouses_df.set_index(
        "warehouse_id"
    )["country"].to_dict()

    for _, order in orders_df.iterrows():

        order_date = order["order_date"]

        if hasattr(order_date, "date"):
            order_date_only = order_date.date()
        else:
            order_date_only = order_date

        # ----------------------------------------------------------
        # Restrict to products that exist as of this order's date
        # ----------------------------------------------------------

        eligible_mask = (
            (launch_dates <= order_date_only)
            & (discontinued_dates >= order_date_only)
        )

        eligible_products = products_df[eligible_mask]

        # ----------------------------------------------------------
        # Further restrict to products the fulfilling warehouse
        # actually carries.
        # ----------------------------------------------------------

        warehouse_id = order["fulfillment_warehouse_id"]

        carried_product_ids = products_by_warehouse.get(
            warehouse_id,
            set(),
        )

        eligible_products = eligible_products[
            eligible_products["product_id"].isin(carried_product_ids)
        ]

        if eligible_products.empty:
            continue

        basket_size = weighted_choice(BASKET_SIZE)

        basket_size = min(basket_size, len(eligible_products))

        basket = _weighted_sample_without_replacement(
            eligible_products,
            n=basket_size,
            weight_col="popularity_weight",
        )

        # ----------------------------------------------------------
        # Tax rate (by fulfilling warehouse's country) and
        # commission rate (by sales channel) are the same for
        # every line item in this order, so compute once per order
        # rather than once per line.
        # ----------------------------------------------------------

        warehouse_country = warehouse_country_lookup.get(warehouse_id)

        tax_rate = TAX_RATES_BY_COUNTRY.get(warehouse_country, 0.0)

        commission_rate = MARKETPLACE_COMMISSION_RATES.get(
            order["sales_channel"],
            0.0,
        )

        for _, product in basket.iterrows():

            quantity = weighted_choice(QUANTITY_WEIGHTS)

            discount_pct = weighted_choice(DISCOUNT_WEIGHTS)

            unit_price = round(product["msrp_sgd"], 2)

            gross_sales = round(quantity * unit_price, 2)

            discount_amount = round(gross_sales * discount_pct, 2)

            net_sales = round(gross_sales - discount_amount, 2)

            tax_amount = round(net_sales * tax_rate, 2)

            commission_amount = round(net_sales * commission_rate, 2)

            records.append(

                {

                    "order_item_id":
                        generate_id("OI", order_item_number, width=9),

                    "order_id":
                        order["order_id"],

                    "product_id":
                        product["product_id"],

                    # Inherited from the order header
                    "warehouse_id":
                        warehouse_id,

                    "quantity":
                        quantity,

                    "unit_price":
                        unit_price,

                    "discount_pct":
                        discount_pct,

                    "gross_sales":
                        gross_sales,

                    "discount_amount":
                        discount_amount,

                    "net_sales":
                        net_sales,

                    "tax_amount":
                        tax_amount,

                    "commission_amount":
                        commission_amount,

                }

            )

            order_item_number += 1

    order_items_df = (
        pd.DataFrame(records)
        .sort_values(["order_id", "order_item_id"])
        .reset_index(drop=True)
    )

    return order_items_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    from customers import generate_customers
    from orders import generate_orders
    from products import generate_products
    from suppliers import generate_suppliers
    from warehouses import generate_warehouses
    from assignment import generate_product_warehouse_assignment

    from utils import assign_demand_tiers

    suppliers_df = generate_suppliers()

    products_df = generate_products(
        suppliers_df=suppliers_df,
    )

    customers_df = generate_customers()

    warehouses_df = generate_warehouses()

    demand_tiers = assign_demand_tiers(products_df)

    assignment_df = generate_product_warehouse_assignment(
        products_df=products_df,
        warehouses_df=warehouses_df,
        demand_tiers=demand_tiers,
    )

    orders_df = generate_orders(
        customers_df=customers_df,
        warehouses_df=warehouses_df,
    )

    order_items_df = generate_order_items(
        orders_df=orders_df,
        products_df=products_df,
        assignment_df=assignment_df,
        warehouses_df=warehouses_df,
    )

    print(order_items_df.head())
    print()
    print(order_items_df.info())