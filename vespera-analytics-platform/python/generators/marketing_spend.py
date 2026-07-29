"""
Marketing Spend Generator

Creates enterprise marketing spend records for the
Vespera Analytics Platform.

This is the data source that makes CAC (Customer Acquisition
Cost), ROAS (Return on Ad Spend), and LTV:CAC Ratio computable —
per the Enterprise KPI Framework, these require marketing spend
joined against customer acquisition events, and no other generator
in this pipeline produces spend data.

Only paid channels (Facebook Ads, Instagram, TikTok, Email
Campaign — see config.MARKETING_CHANNELS) get spend rows. Organic
Search and Referral are intentionally excluded, since they're
unpaid acquisition paths; customers.py still assigns customers to
them, so they correctly contribute to the "new customers"
denominator in CAC without a matching spend numerator.

Spend is generated at the grain of one row per (date, campaign),
which rolls up cleanly to date/channel/platform for the KPI
framework's required reporting grain.
"""

from __future__ import annotations

import random

import pandas as pd

from config import (
    RANDOM_SEED,
    SIMULATION_START_DATE,
    SIMULATION_END_DATE,
    MARKETING_CHANNELS,
    SEASONALITY_MULTIPLIERS,
)

from utils import generate_id

# =============================================================================
# CONFIGURATION
# =============================================================================

CAMPAIGNS_PER_CHANNEL_RANGE = (4, 8)

CAMPAIGN_DURATION_DAYS_RANGE = (14, 45)

# Cost per thousand impressions (CPM), in SGD. Used to derive
# impressions from spend so the table carries believable
# impressions/clicks/CTR fields, not just a dollar amount.
CPM_RANGE = (5.0, 15.0)

CLICK_THROUGH_RATE_RANGE = (0.008, 0.035)

# Daily spend variance around the campaign's base daily budget, so
# spend isn't perfectly flat across a campaign's run.
DAILY_SPEND_VARIANCE = (0.75, 1.25)

CAMPAIGN_THEMES = [
    "Brand Awareness",
    "New Arrivals",
    "Flash Sale",
    "Retargeting",
    "Holiday Push",
    "Category Spotlight",
    "Loyalty Drive",
    "Regional Launch",
]


# =============================================================================
# HELPERS
# =============================================================================

def _build_campaigns(seed: int) -> list[dict]:
    """
    Generate a campaign calendar: for each paid channel, a handful
    of campaigns with randomized start/end dates and a base daily
    budget within that channel's configured range.
    """

    random.seed(seed)

    simulation_days = (
        SIMULATION_END_DATE - SIMULATION_START_DATE
    ).days

    campaigns = []

    campaign_number = 1

    for channel, channel_cfg in MARKETING_CHANNELS.items():

        num_campaigns = random.randint(*CAMPAIGNS_PER_CHANNEL_RANGE)

        for _ in range(num_campaigns):

            duration = random.randint(*CAMPAIGN_DURATION_DAYS_RANGE)

            latest_start = max(simulation_days - duration, 0)

            start_offset = random.randint(0, latest_start)

            start_date = SIMULATION_START_DATE + pd.Timedelta(
                days=start_offset
            )

            end_date = min(
                start_date + pd.Timedelta(days=duration),
                SIMULATION_END_DATE,
            )

            theme = random.choice(CAMPAIGN_THEMES)

            daily_budget = random.uniform(
                *channel_cfg["daily_budget_range"]
            )

            campaigns.append(

                {

                    "campaign_id":
                        generate_id("CMP", campaign_number, width=4),

                    "campaign_name":
                        f"{channel} - {theme} {campaign_number}",

                    "channel":
                        channel,

                    "platform":
                        channel_cfg["platform"],

                    "start_date":
                        start_date,

                    "end_date":
                        end_date,

                    "daily_budget":
                        daily_budget,

                }

            )

            campaign_number += 1

    return campaigns


# =============================================================================
# GENERATOR
# =============================================================================

def generate_marketing_spend(
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate enterprise marketing spend records.

    Returns
    -------
    pandas.DataFrame
        One row per (date, campaign). Rolls up to date/channel/
        platform for CAC, ROAS, and LTV:CAC reporting.
    """

    random.seed(seed)

    campaigns = _build_campaigns(seed)

    records = []

    spend_number = 1

    for campaign in campaigns:

        current_date = campaign["start_date"]

        while current_date <= campaign["end_date"]:

            seasonality = SEASONALITY_MULTIPLIERS.get(
                current_date.month,
                1.0,
            )

            spend_variance = random.uniform(*DAILY_SPEND_VARIANCE)

            spend = round(
                campaign["daily_budget"]
                * seasonality
                * spend_variance,
                2,
            )

            cpm = random.uniform(*CPM_RANGE)

            impressions = int((spend / cpm) * 1000)

            click_through_rate = round(
                random.uniform(*CLICK_THROUGH_RATE_RANGE),
                4,
            )

            clicks = int(impressions * click_through_rate)

            cost_per_click = (
                round(spend / clicks, 2) if clicks > 0 else 0.0
            )

            records.append(

                {

                    "marketing_spend_id":
                        generate_id("MKT", spend_number, width=8),

                    "date":
                        current_date.date(),

                    "campaign_id":
                        campaign["campaign_id"],

                    "campaign_name":
                        campaign["campaign_name"],

                    "channel":
                        campaign["channel"],

                    "platform":
                        campaign["platform"],

                    "spend_sgd":
                        spend,

                    "impressions":
                        impressions,

                    "clicks":
                        clicks,

                    "click_through_rate":
                        click_through_rate,

                    "cost_per_click_sgd":
                        cost_per_click,

                }

            )

            spend_number += 1

            current_date += pd.Timedelta(days=1)

    marketing_spend_df = (
        pd.DataFrame(records)
        .sort_values(["date", "campaign_id"])
        .reset_index(drop=True)
    )

    return marketing_spend_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    marketing_spend_df = generate_marketing_spend()

    print(marketing_spend_df.head())
    print()
    print(
        marketing_spend_df.groupby("channel")["spend_sgd"]
        .sum()
        .sort_values(ascending=False)
    )
    print()
    print(f"Total spend: SGD {marketing_spend_df['spend_sgd'].sum():,.2f}")
    print()
    print(marketing_spend_df.info())