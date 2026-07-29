"""
Shipment Generator

Creates enterprise shipment records for the
Vespera Analytics Platform.

Shipments are generated from fulfilled customer
orders and represent the outbound logistics process.
"""

from __future__ import annotations

from datetime import timedelta
import random

import pandas as pd

from config import RANDOM_SEED

from utils import weighted_choice, generate_id

# =============================================================================
# CONFIGURATION
# =============================================================================

CARRIERS = {

    "DHL": 0.20,

    "FedEx": 0.15,

    "J&T Express": 0.25,

    "Ninja Van": 0.20,

    "LBC Express": 0.10,

    "GrabExpress": 0.10,

}

SERVICE_LEVEL = {

    "Standard": 0.75,

    "Express": 0.20,

    "Same Day": 0.05,

}

# Shipment status is derived from the order's own order_status
# rather than sampled independently, so the two facts can't
# contradict each other (e.g. an order marked "Delivered" whose
# shipment says "Failed Delivery").

DELIVERED_ORDER_SHIPMENT_STATUS = {

    "Delivered": 0.97,

    "Failed Delivery": 0.03,

}

SHIPPED_ORDER_SHIPMENT_STATUS = {

    "In Transit": 0.55,

    "Delivered": 0.45,

}

# Base shipping cost by service level, before any cross-border
# surcharge is applied.

BASE_SHIPPING_COST_RANGE = {

    "Standard": (3.50, 8.00),

    "Express": (7.00, 14.00),

    "Same Day": (12.00, 20.00),

}

CROSS_BORDER_SURCHARGE = (6.00, 15.00)


# =============================================================================
# GENERATOR
# =============================================================================

def generate_shipments(
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    warehouses_df: pd.DataFrame,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate enterprise shipment records.

    Requires customers_df and warehouses_df so shipping cost can
    reflect whether a shipment crosses a country border (customer
    country != fulfilling warehouse's country).
    """

    random.seed(seed)

    fulfilled_orders = orders_df[
        orders_df["order_status"].isin(["Shipped", "Delivered"])
    ].copy()

    fulfilled_orders = fulfilled_orders.merge(
        customers_df[["customer_id", "country"]].rename(
            columns={"country": "customer_country"}
        ),
        on="customer_id",
        how="left",
    )

    fulfilled_orders = fulfilled_orders.merge(
        warehouses_df[["warehouse_id", "country"]].rename(
            columns={
                "warehouse_id": "fulfillment_warehouse_id",
                "country": "warehouse_country",
            }
        ),
        on="fulfillment_warehouse_id",
        how="left",
    )

    records = []

    shipment_number = 1

    for _, order in fulfilled_orders.iterrows():

        order_date = pd.to_datetime(order["order_date"])

        service_level = weighted_choice(SERVICE_LEVEL)

        if service_level == "Same Day":

            ship_delay = 0
            delivery_days = 0

        elif service_level == "Express":

            ship_delay = 0
            delivery_days = random.randint(1, 2)

        else:

            ship_delay = random.randint(0, 1)
            delivery_days = random.randint(3, 7)

        shipped_date = order_date + timedelta(days=ship_delay)

        # ----------------------------------------------------------
        # Shipment status derived from order_status, not sampled
        # independently — keeps the two facts consistent with
        # each other.
        # ----------------------------------------------------------

        if order["order_status"] == "Delivered":
            shipment_status = weighted_choice(
                DELIVERED_ORDER_SHIPMENT_STATUS
            )
        else:
            shipment_status = weighted_choice(
                SHIPPED_ORDER_SHIPMENT_STATUS
            )

        delivered_date = shipped_date + timedelta(days=delivery_days)

        carrier = weighted_choice(CARRIERS)

        # ----------------------------------------------------------
        # Shipping cost: base range by service level, plus a
        # surcharge if the shipment crosses a country border.
        # ----------------------------------------------------------

        cost_min, cost_max = BASE_SHIPPING_COST_RANGE[service_level]

        shipping_cost = random.uniform(cost_min, cost_max)

        is_cross_border = (
            order["customer_country"] != order["warehouse_country"]
        )

        if is_cross_border:
            shipping_cost += random.uniform(*CROSS_BORDER_SURCHARGE)

        shipping_cost = round(shipping_cost, 2)

        records.append(

            {

                "shipment_id":
                    generate_id("SHP", shipment_number, width=8),

                "order_id":
                    order["order_id"],

                "warehouse_id":
                    order["fulfillment_warehouse_id"],

                "carrier":
                    carrier,

                "tracking_number":
                    generate_id("TRK", shipment_number, width=10),

                "service_level":
                    service_level,

                "shipment_status":
                    shipment_status,

                "is_cross_border":
                    is_cross_border,

                "shipped_date":
                    shipped_date,

                "delivered_date":
                    delivered_date
                    if shipment_status == "Delivered"
                    else pd.NaT,

                "shipping_cost":
                    shipping_cost,

            }

        )

        shipment_number += 1

    shipments_df = (
        pd.DataFrame(records)
        .sort_values("shipped_date")
        .reset_index(drop=True)
    )

    return shipments_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    from customers import generate_customers
    from warehouses import generate_warehouses
    from orders import generate_orders

    customers_df = generate_customers()

    warehouses_df = generate_warehouses()

    orders_df = generate_orders(
        customers_df=customers_df,
        warehouses_df=warehouses_df,
    )

    shipments_df = generate_shipments(
        orders_df=orders_df,
        customers_df=customers_df,
        warehouses_df=warehouses_df,
    )

    print(shipments_df.head())
    print()
    print(shipments_df["shipment_status"].value_counts())
    print()
    print(shipments_df.info())