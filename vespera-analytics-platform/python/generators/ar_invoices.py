"""
AR Invoices Generator

Creates invoice-level accounts receivable records for a subset of
orders settled on credit terms rather than immediate payment.

Source for fact_ar_aging_daily. Added as part of the KPI Framework
<-> Star Schema reconciliation (v1.2) to close the DSO data gap —
see docs/06_kpi_schema_reconciliation.md.

SIMPLIFICATION NOTE: Vespera's customer base is modeled as pure B2C
(no wholesale/B2B segment exists in customers.py). Per project
decision, this generator assigns credit terms to a small random
subset of orders against existing retail customers rather than
modeling a separate wholesale account type. This is a known
simplification, not a claim that individual loyalty customers
realistically get NET30 terms — see reconciliation doc Section 5
for the open scoping question this leaves for Finance.

This generator ALSO decides payment_terms_code per order (the
degenerate dimension added to fact_sales in the v1.2 schema
update), output alongside invoices as a separate bridge so
orders.py doesn't need to be modified — dbt merges it into
fact_sales at build time.

Depends on orders.py's generate_orders() and order_items.py's
generate_order_items() output.
"""

from __future__ import annotations

import random

import pandas as pd

from config import (
    RANDOM_SEED,
    SIMULATION_END_DATE,
    PCT_ORDERS_ON_CREDIT_TERMS,
    PAYMENT_TERMS_WEIGHTS,
    PAYMENT_TERMS_DAYS,
    INVOICE_OUTCOME_WEIGHTS,
)

from utils import weighted_choice, generate_id, money

# Only outcomes other than "Still Open" are valid once an invoice's
# due date is more than this many days in the past relative to the
# simulation end — an invoice genuinely still open 90+ days past due
# would normally have gone to collections/write-off, not just sit
# there, so we resample toward a resolved outcome instead.
STILL_OPEN_ELIGIBILITY_WINDOW_DAYS = 60


# =============================================================================
# HELPERS
# =============================================================================

def _resolve_outcome(due_date: pd.Timestamp) -> str:
    """
    Sample an invoice outcome, but disallow "Still Open" for
    invoices whose due date is too far in the past to plausibly
    still be sitting unpaid and untouched.
    """

    outcome = weighted_choice(INVOICE_OUTCOME_WEIGHTS)

    days_past_due = (SIMULATION_END_DATE - due_date).days

    if outcome == "Still Open" and days_past_due > STILL_OPEN_ELIGIBILITY_WINDOW_DAYS:

        resolved_weights = {

            key: weight
            for key, weight in INVOICE_OUTCOME_WEIGHTS.items()
            if key != "Still Open"

        }

        total = sum(resolved_weights.values())

        resolved_weights = {
            key: weight / total
            for key, weight in resolved_weights.items()
        }

        outcome = weighted_choice(resolved_weights)

    return outcome


def _resolve_payment(
    invoice_date: pd.Timestamp,
    due_date: pd.Timestamp,
    invoice_amount: float,
    outcome: str,
) -> tuple:
    """
    Given an outcome, compute (payment_date, amount_paid,
    invoice_status). payment_date is None for still-open invoices.
    """

    if outcome == "Paid On Time":

        terms_days = max((due_date - invoice_date).days, 1)

        payment_date = due_date - pd.Timedelta(
            days=random.randint(0, terms_days)
        )

        payment_date = max(payment_date, invoice_date)

        return payment_date, money(invoice_amount), "Paid"

    if outcome == "Paid Late":

        payment_date = due_date + pd.Timedelta(
            days=random.randint(1, 45)
        )

        payment_date = min(payment_date, SIMULATION_END_DATE)

        return payment_date, money(invoice_amount), "Paid"

    if outcome == "Partially Paid":

        payment_date = due_date + pd.Timedelta(
            days=random.randint(-5, 20)
        )

        payment_date = min(
            max(payment_date, invoice_date),
            SIMULATION_END_DATE,
        )

        partial_fraction = random.uniform(0.30, 0.80)

        return (
            payment_date,
            money(invoice_amount * partial_fraction),
            "Partially Paid",
        )

    # Still Open
    return None, 0.0, "Open"


# =============================================================================
# GENERATOR
# =============================================================================

def generate_ar_invoices(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    pct_orders_on_credit_terms: float = PCT_ORDERS_ON_CREDIT_TERMS,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Select a random subset of orders to be invoiced on credit terms
    and simulate their payment lifecycle.

    Only orders with an "order_status" that implies the sale
    actually completed (i.e. not "Cancelled") are eligible, since a
    cancelled order shouldn't generate a receivable.

    Returns
    -------
    pandas.DataFrame — one row per invoiced order, with payment_terms_code
    included so it can also be merged back into fact_sales.
    """

    random.seed(seed)

    order_totals = (
        order_items_df
        .groupby("order_id")["net_sales"]
        .sum()
        .rename("invoice_amount")
        .reset_index()
    )

    eligible_orders = (
        orders_df[orders_df["order_status"] != "Cancelled"]
        .merge(order_totals, on="order_id", how="inner")
    )

    sampled_orders = eligible_orders.sample(
        frac=pct_orders_on_credit_terms,
        random_state=seed,
    )

    records = []

    invoice_number = 1

    for _, order in sampled_orders.iterrows():

        payment_terms_code = weighted_choice(PAYMENT_TERMS_WEIGHTS)

        terms_days = PAYMENT_TERMS_DAYS[payment_terms_code]

        invoice_date = (
            pd.Timestamp(order["order_date"])
            + pd.Timedelta(days=random.randint(0, 3))
        )

        due_date = invoice_date + pd.Timedelta(days=terms_days)

        outcome = _resolve_outcome(due_date)

        payment_date, amount_paid, invoice_status = _resolve_payment(
            invoice_date=invoice_date,
            due_date=due_date,
            invoice_amount=order["invoice_amount"],
            outcome=outcome,
        )

        records.append(

            {

                "invoice_id":
                    generate_id("INV", invoice_number, width=7),

                "order_id":
                    order["order_id"],

                "customer_id":
                    order["customer_id"],

                "payment_terms_code":
                    payment_terms_code,

                "invoice_date":
                    invoice_date.date(),

                "due_date":
                    due_date.date(),

                "invoice_amount":
                    money(order["invoice_amount"]),

                "amount_paid":
                    amount_paid,

                "payment_date":
                    payment_date.date() if payment_date is not None else None,

                "invoice_status":
                    invoice_status,

            }

        )

        invoice_number += 1

    invoices_df = (
        pd.DataFrame(records)
        .sort_values("invoice_id")
        .reset_index(drop=True)
    )

    return invoices_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    from customers import generate_customers
    from warehouses import generate_warehouses
    from orders import generate_orders
    from order_items import generate_order_items

    customers_df = generate_customers()
    warehouses_df = generate_warehouses()

    orders_df = generate_orders(
        customers_df=customers_df,
        warehouses_df=warehouses_df,
    )

    # order_items.py's generator additionally needs products/assignment
    # data in the real pipeline — see generate_data.py for the full
    # wiring. This standalone example assumes it's available.
    order_items_df = generate_order_items(
        orders_df=orders_df,
    )

    invoices_df = generate_ar_invoices(
        orders_df=orders_df,
        order_items_df=order_items_df,
    )

    print(invoices_df.head())
    print()
    print(f"Invoiced orders: {len(invoices_df):,}")
    print()
    print(invoices_df["invoice_status"].value_counts())
    print()
    print(invoices_df["payment_terms_code"].value_counts())
    print()
    print(invoices_df.info())