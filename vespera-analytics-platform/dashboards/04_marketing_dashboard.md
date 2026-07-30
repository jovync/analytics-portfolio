# Marketing Dashboard — Looker Studio Design Specification

## Purpose

The Marketing Dashboard gives the Marketing Director and Head of Growth a view of acquisition efficiency and long-term customer value — connecting ad spend to the revenue it actually produces, rather than platform-reported vanity metrics.

**Audience:** Marketing Director, Head of Growth, Campaign Managers
**Cadence:** Daily for spend/CAC; monthly for LTV and LTV:CAC (matches KPI Framework reporting grain)
**Governing principle:** All metrics trace to the Enterprise KPI Framework. LTV is sourced from `fact_sales`. CAC now traces to `fact_marketing_spend`, added in the v1.2 schema reconciliation, with attribution resolved via `dim_customer.acquisition_campaign_key` (see `06_kpi_schema_reconciliation.md`). **Pages 3–4 are unblocked as of this update** — Section 6 below records the resolved gap for traceability rather than as an open blocker.

---

## 1. Data Source Strategy

| Looker Studio Data Source | Underlying dbt Mart | Grain | Refresh |
|---|---|---|---|
| `marketing_ltv_cohort` | `mart_customer_ltv` (built on `fact_sales` + `dim_customer`) | Customer Cohort × Month | Monthly |
| `marketing_channel_revenue` | `mart_sales_summary` (filtered/grouped by `dim_customer.acquisition_channel_name`) | Date × Acquisition Channel | Daily |
| `marketing_spend_cac` | `mart_marketing_spend_cac` (built on `fact_marketing_spend` + `dim_campaign` + `dim_customer.acquisition_campaign_key`) | Date × Campaign × Platform | Daily |
| `marketing_ltv_cac_ratio` | `mart_marketing_spend_cac` joined to `mart_customer_ltv` | Month × Acquisition Channel | Monthly |

**Note on attribution:** CAC's "new customers" count comes from `dim_customer` rows where `acquisition_campaign_key` matches the campaign in question — first-touch attribution set at the customer's first-ever order, per the reconciliation memo's Option B. `fact_marketing_spend.platform_reported_conversions_count` is retained for reconciliation against this first-party count, not used as CAC's source of truth.

---

## 2. Report Structure (Pages)

```
Page 1 — Customer Value Overview        (default landing page)
Page 2 — Revenue & LTV by Channel
Page 3 — Acquisition Cost & Efficiency
Page 4 — Campaign-Level Performance
```

Persistent filter panel: date range, acquisition channel, customer cohort — applies report-wide.

---

## 3. Page-by-Page Design

### Page 1 — Customer Value Overview

Scorecards:

| Metric | Formula (per KPI Framework) | Owner | Status |
|---|---|---|---|
| Customer Lifetime Value (LTV) | Sum(Customer Gross Margin) | Head of Growth | ✅ Buildable |
| New Customers (period) | Count of first-purchase customers | Head of Growth | ✅ Buildable |
| Customer Acquisition Cost (CAC) | Marketing Spend ÷ New Customers | Marketing Director | ✅ Buildable *(v1.2)* |
| LTV:CAC Ratio | LTV ÷ CAC | Marketing Director | ✅ Buildable *(v1.2)* |

- Line chart: LTV trend by monthly customer cohort (cohorts shown as separate lines, revealing how value compounds or decays over time)
- Bar chart: New Customers by month
- CAC and LTV:CAC scorecards now render live values, sourced from `mart_marketing_spend_cac`

### Page 2 — Revenue & LTV by Channel

- Bar chart: LTV by Acquisition Channel (from `dim_customer.acquisition_channel_name`)
- Bar chart: Net Revenue by Acquisition Channel
- Table: Customer count, average LTV, and average order frequency by Acquisition Channel
- Cohort heat-map: LTV by acquisition month × months-since-acquisition (classic cohort retention/value grid)

### Page 3 — Acquisition Cost & Efficiency

- Scorecards: CAC, LTV:CAC Ratio
- Line chart: CAC trend by Acquisition Channel, sourced from `fact_marketing_spend` aggregated by `dim_campaign.marketing_platform` and joined to `dim_customer.acquisition_campaign_key`
- Scatter plot: CAC vs. LTV by channel (visually flags channels where LTV:CAC is bad)
- Bar chart: LTV:CAC Ratio by channel with a "healthy" reference line at 3:1
- Data-quality note tile: variance between `platform_reported_conversions_count` and first-party `dim_customer` attribution counts, so Marketing can sanity-check platform-reported numbers against the governed figure rather than silently trusting either

### Page 4 — Campaign-Level Performance

- Table: Campaign-level Spend, New Customers, CAC, sorted worst-to-best for quick triage — grain matches `fact_marketing_spend`'s Date × Campaign × Platform declared grain
- Bar chart: Spend by Platform (Meta, Google, TikTok), from `fact_marketing_spend.spend_amount`
- Trend: Spend vs. New Customers Acquired, by week
- Table: Campaigns with spend but zero attributed new customers (`acquisition_campaign_key` never matched) — surfaces attribution gaps or genuinely underperforming campaigns for follow-up

---

## 4. Calculated Fields (Looker Studio syntax)

```
LTV (customer-level, buildable today):
SUM(net_revenue_amount) - SUM(cogs_amount)     -- per customer, summed over full history

New Customer Flag (first-purchase detection):
CASE WHEN order_date_key = MIN(order_date_key) OVER (PARTITION BY customer_sk) THEN 1 ELSE 0 END

CAC (by campaign or channel):
SUM(spend_amount) / COUNT(DISTINCT customer_sk WHERE acquisition_campaign_key = campaign_key)

LTV:CAC Ratio:
SUM(ltv_amount) / SUM(cac_amount)

LTV:CAC Health Flag:
CASE
  WHEN ltv_cac_ratio >= 3 THEN "Healthy"
  WHEN ltv_cac_ratio >= 1.5 THEN "Marginal"
  ELSE "Unprofitable"
END

Attribution Gap Flag (Page 4):
CASE WHEN spend_amount > 0 AND new_customers_count = 0 THEN "⚠ No Attributed Customers" ELSE "OK" END
```

---

## 5. Filters & Controls

| Control | Type | Applies To |
|---|---|---|
| Date Range | Date range control | All pages |
| Acquisition Channel | Drop-down (multi-select) | Pages 1–3 |
| Customer Cohort (month) | Drop-down | Pages 1, 2 |
| Campaign | Drop-down | Page 4 |
| Marketing Platform | Drop-down | Pages 3, 4 |

---

## 6. Resolved Data Gap — Marketing Spend / CAC *(Closed in v1.2 schema reconciliation)*

The KPI Framework defines CAC as `Marketing Spend ÷ New Customers`, sourced from Meta, Google, TikTok, and Shopify, owned by the Marketing Director. The original star schema had no fact table capturing marketing spend — none of the five original fact tables carried ad platform cost data.

**This was closed via schema reconciliation** (`06_kpi_schema_reconciliation.md`):
1. New **`fact_marketing_spend`** transaction fact (grain: Date × Campaign × Platform), sourced from Meta/Google/TikTok ad platform APIs — see `03_star_schema.md` Section 6.7.
2. New **`dim_campaign`** conformed dimension for campaign metadata.
3. **Attribution model decided: first-touch (Option B).** `dim_customer.acquisition_campaign_key` is set at the customer's first-ever order, reusing the pattern already established by `acquisition_channel_name`. Multi-touch attribution (Option C) remains a documented future enhancement, not a current blocker — Vespera doesn't yet capture clickstream-level touchpoint data to support it.

This mirrors how the DSO gap was resolved on the Finance Dashboard — same schema reconciliation pass closed both.

---

## 7. Interactivity & Navigation

- Cross-filtering enabled within each page
- Drill link back to Executive Dashboard's Customer & Marketing Efficiency page
- Cohort heat-map (Page 2) links to Page 1's LTV trend chart, filtered to the clicked cohort

---

## 8. Visual & Governance Standards

- Same shared Looker Studio theme as Executive, Supply Chain, and Finance dashboards
- Chart titles use official KPI Framework names
- Every page footer shows: source mart name, last refresh timestamp, KPI Framework version
- **Attribution transparency:** since CAC relies on first-touch attribution rather than platform-reported conversions, any tile showing CAC or LTV:CAC should make the attribution methodology visible (e.g., a footnote or info-icon), so stakeholders don't mistake it for platform-native numbers they may see elsewhere

---

## 9. Open Items for Build Phase

- [ ] Confirm `mart_customer_ltv` and `mart_marketing_spend_cac` exist and pass dbt tests
- [ ] Define LTV:CAC healthy-ratio threshold with Marketing Director (3:1 used as placeholder above)
- [ ] Confirm Meta/Google/TikTok API ingestion pipelines are built and landing into `fact_marketing_spend` on schedule
- [ ] Validate `acquisition_campaign_key` backfill on historical `dim_customer` records — first-touch attribution needs UTM/click-tracking data captured at original signup, which may not exist for older customer records
- [ ] Monitor the variance between platform-reported conversions and first-party attribution counts during initial rollout, to catch attribution logic bugs early