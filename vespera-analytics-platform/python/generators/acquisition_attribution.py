"""
Customer Acquisition Attribution Generator

Creates the bridge between customers and the marketing campaign
that acquired them, using first-touch attribution set at the
customer's signup date.

This is an additive bridge table, not a modification to
dim_customer's source — dbt joins it into dim_customer as
acquisition_campaign_key at the intermediate model layer, per the
attribution model decision in
docs/06_kpi_schema_reconciliation.md (Section 3.3, Option B).

Paid channels (see config.MARKETING_CHANNELS: Facebook Ads,
Instagram, TikTok, Email Campaign) are eligible for attribution.
Organic Search and Referral are unpaid/indirect acquisition paths —
customers.py's ACQUISITION_CHANNELS still assigns customers to
them, but they intentionally receive no campaign attribution here.
This is what keeps CAC math meaningful: organic/referral customers
count in the "new customers" denominator without a spend numerator
to match.

Depends on customers.py's generate_customers() and
marketing_spend.py's generate_marketing_spend() output. Campaign
date windows are derived directly from the exploded spend records
(grouped by campaign_id) rather than requiring a separate campaign
calendar export, since marketing_spend.py's campaign builder is a
private helper.
"""

from __future__ import annotations

import pandas as pd

from config import RANDOM_SEED, MARKETING_CHANNELS


# =============================================================================
# HELPERS
# =============================================================================

def _derive_campaign_windows(marketing_spend_df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse the exploded (date, campaign) spend records back into
    one row per campaign with its active date range and channel,
    since that's the granularity attribution needs.
    """

    return (
        marketing_spend_df
        .groupby(["campaign_id", "channel"])["date"]
        .agg(start_date="min", end_date="max")
        .reset_index()
    )


# =============================================================================
# GENERATOR
# =============================================================================

def generate_acquisition_attribution(
    customers_df: pd.DataFrame,
    marketing_spend_df: pd.DataFrame,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Assign each paid-channel customer to the most recent campaign on
    their acquisition channel that had already launched on or before
    their signup date — a first-touch rule that doesn't require the
    campaign to still be running at signup, since real conversions
    can lag well past a campaign's active window.

    Customers whose signup date predates every campaign on their
    channel, or whose acquisition_channel is unpaid (Organic Search,
    Referral), are left unattributed (acquisition_campaign_id =
    None), which is the correct outcome for those cases rather than
    a gap to fill.

    Returns
    -------
    pandas.DataFrame with columns [customer_id, acquisition_campaign_id]
    — one row per customer (including unattributed ones), for a
    clean dbt left join.
    """

    # Deterministic given customers_df and marketing_spend_df — no
    # randomness left in the attribution rule itself. seed kept in
    # the signature for interface consistency with the rest of the
    # generator suite.

    paid_channels = set(MARKETING_CHANNELS.keys())

    campaign_windows = _derive_campaign_windows(marketing_spend_df)

    campaigns_by_channel = {

        channel: (
            campaign_windows[campaign_windows["channel"] == channel]
            .sort_values("start_date")
            .reset_index(drop=True)
        )

        for channel in paid_channels

    }

    records = []

    for _, customer in customers_df.iterrows():

        channel = customer["acquisition_channel"]

        signup_date = pd.Timestamp(customer["customer_since"])

        acquisition_campaign_id = None

        if channel in paid_channels:

            eligible = campaigns_by_channel[channel]

            # First-touch attribution: the most recent campaign on
            # this channel that had already launched by signup date.
            # Deliberately NOT requiring the campaign to still be
            # "active" (end_date >= signup) — a customer can be
            # influenced by a campaign and convert well after it
            # stopped spending. Requiring strict overlap was too
            # strict given these are short (14-45 day), sparse
            # campaigns (~25% date coverage per channel) spread
            # across a 2-year window; nearest-prior-campaign is the
            # more realistic rule and matches far more customers.
            prior_campaigns = eligible[
                pd.to_datetime(eligible["start_date"]) <= signup_date
            ]

            if not prior_campaigns.empty:

                acquisition_campaign_id = prior_campaigns.iloc[-1]["campaign_id"]

        records.append(

            {

                "customer_id":
                    customer["customer_id"],

                "acquisition_campaign_id":
                    acquisition_campaign_id,

            }

        )

    attribution_df = (
        pd.DataFrame(records)
        .sort_values("customer_id")
        .reset_index(drop=True)
    )

    return attribution_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    from customers import generate_customers
    from marketing_spend import generate_marketing_spend

    customers_df = generate_customers()
    marketing_spend_df = generate_marketing_spend()

    attribution_df = generate_acquisition_attribution(
        customers_df=customers_df,
        marketing_spend_df=marketing_spend_df,
    )

    attributed_pct = (
        attribution_df["acquisition_campaign_id"].notna().mean() * 100
    )

    print(attribution_df.head())
    print()
    print(f"Attributed: {attributed_pct:.1f}% of customers")
    print()
    print(attribution_df.info())