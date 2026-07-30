# Executive Dashboard — Looker Studio Design Specification

## Purpose

The Executive Dashboard is the single top-level view for C-suite and VP stakeholders at Vespera Lifestyle Group. It answers one question fast: **"Is the business healthy right now, and where is it moving?"** It does not replace the departmental dashboards (Supply Chain, Finance, Marketing) — it summarizes across them and links out for drill-down.

**Audience:** CEO, COO, CFO, VP Supply Chain, VP Marketing, Head of Growth
**Cadence:** Daily refresh, reviewed weekly in leadership sync
**Governing principle:** Every metric shown here traces back to the Enterprise KPI Framework — no dashboard-local calculation logic.

---

## 1. Data Source Strategy

Looker Studio should never join raw fact/dim tables directly — it should read from a **pre-aggregated semantic mart** built in dbt, so calculation logic stays governed in the transformation layer rather than reinvented in the BI tool.

| Looker Studio Data Source | Underlying dbt Mart | Grain | Refresh |
|---|---|---|---|
| `exec_kpi_daily` | `mart_executive_kpi_daily` | Date × Channel | Daily |
| `exec_revenue_trend` | `mart_sales_summary` | Date × Channel × Region | Daily |
| `exec_margin_summary` | `mart_finance_summary` | Date × Product Category | Daily |
| `exec_inventory_health` | `mart_inventory_summary` | Date × Warehouse | Every 4 hrs (per WMS sync) |
| `exec_marketing_efficiency` | `mart_marketing_summary` | Month × Acquisition Channel | Daily |

Connection type: **BigQuery custom query / native mart tables**, not a live raw-table blend — this keeps dashboard load fast and avoids Looker Studio's blend-node row limits.

**Data freshness caveat to surface in the UI:** because WMS↔e-commerce sync runs every 4 hours and marketplace reconciliation completes at month-end close, the Inventory and Marketplace Revenue tiles should carry a small "as of" timestamp caption rather than imply real-time accuracy.

---

## 2. Report Structure (Pages)

```
Page 1 — Overview Scorecard        (default landing page)
Page 2 — Revenue & Growth Trend
Page 3 — Profitability
Page 4 — Channel & Regional Performance
Page 5 — Customer & Marketing Efficiency
Page 6 — Supply Chain Pulse (summary only, links to full Supply Chain Dashboard)
```

A persistent left-side **filter panel** (date range, channel, region) applies across all pages via Looker Studio's report-level filter controls.

---

## 3. Page-by-Page Design

### Page 1 — Overview Scorecard

Top-row scorecards (single-value tiles with trend arrow + % change vs. prior period):

| Metric | Formula (per KPI Framework) | Owner |
|---|---|---|
| Net Revenue | Gross Sales − Discounts − Returns − Taxes | Head of Finance |
| Gross Margin % | (Net Revenue − COGS) ÷ Net Revenue | Head of Finance |
| AOV | Net Revenue ÷ Completed Orders | Head of E-Commerce |
| Return Rate | Returned Units ÷ Sold Units | Customer Experience Lead |
| Stockout Rate | Stockout SKUs ÷ Active SKUs | VP Supply Chain |
| LTV:CAC Ratio | LTV ÷ CAC | Marketing Director |

Below the scorecard row: a **combo chart** (bar = Net Revenue, line = Gross Margin %) trended daily for the last 90 days, with a date-range comparison toggle (this period vs. last period, YoY).

### Page 2 — Revenue & Growth Trend

- Time-series line chart: Net Revenue by day, broken out by Sales Channel (Shopify Plus, Shopify POS, Shopee/Lazada)
- Bar chart: AOV by channel
- Table: Top 10 SKUs by Net Revenue with sparkline trend column
- Annotation layer: promotion windows overlaid on the trend line (from `dim_promotion`) so revenue spikes are explainable

### Page 3 — Profitability

- Scorecard row: Gross Margin %, COGS, Net Revenue, DSO
- Bar chart: Gross Margin % by Product Category
- Geo map: Gross Margin % by Country
- Table: Margin by Channel with conditional formatting (red/yellow/green vs. target)

### Page 4 — Channel & Regional Performance

- Geo map: Net Revenue by Country/Region
- Stacked bar: Revenue mix by Channel Class (Retail Boutique / Web / Marketplace)
- Scorecard comparison: Online vs. Retail vs. Marketplace AOV and Return Rate side-by-side

### Page 5 — Customer & Marketing Efficiency

- Scorecards: CAC, LTV, LTV:CAC Ratio
- Line chart: CAC trend by Acquisition Channel (Meta, Google, TikTok)
- Bar chart: LTV by Customer Cohort (monthly cohorts)
- Table: Campaign-level CAC vs. LTV:CAC, sorted worst-to-best for quick triage

### Page 6 — Supply Chain Pulse (summary card, not full detail)

- Scorecards: Inventory Turnover, Stockout Rate
- Bar chart: Stockout Rate by Warehouse
- "As of [timestamp]" freshness caption per the 4-hour sync constraint
- Button/link element → full Supply Chain Dashboard

---

## 4. Calculated Fields (Looker Studio syntax)

Even though logic is governed upstream in dbt, a few presentation-layer calculated fields are still needed for comparisons and formatting:

```
% Change vs. Prior Period:
(SUM(net_revenue) - SUM(net_revenue_prior_period)) / SUM(net_revenue_prior_period)

Margin Status Flag:
CASE
  WHEN gross_margin_pct >= 0.45 THEN "On Target"
  WHEN gross_margin_pct >= 0.35 THEN "Watch"
  ELSE "Below Target"
END

LTV:CAC Health Flag:
CASE
  WHEN ltv_cac_ratio >= 3 THEN "Healthy"
  WHEN ltv_cac_ratio >= 1.5 THEN "Marginal"
  ELSE "Unprofitable"
END
```

---

## 5. Filters & Controls

| Control | Type | Applies To |
|---|---|---|
| Date Range | Date range control | All pages |
| Sales Channel | Drop-down (multi-select) | Pages 1–4 |
| Region/Country | Drop-down | Pages 1, 3, 4 |
| Product Category | Drop-down | Pages 3, 4 |
| Comparison Period | Date range comparison control | Page 1, 2 |

---

## 6. Interactivity & Navigation

- **Cross-filtering:** enabled on all charts within a page (click a channel in the bar chart → filters the scorecards)
- **Drill paths:** each summary page (3–6) includes a linked button to its full departmental dashboard (Finance, Marketing, Supply Chain) for root-cause investigation
- **Alerts:** conditional formatting (red text/icon) on any scorecard breaching its target threshold, defined per KPI owner

---

## 7. Visual & Governance Standards

- One shared **Looker Studio theme** (color palette, font) reused across all four dashboards for brand consistency
- Chart titles always state the metric's official KPI Framework name — never an ad hoc label
- Every page footer includes: data source mart name, last refresh timestamp, and KPI Framework version
- No dashboard-local metric is permitted; if a page needs a new metric, it must first be added to `05_enterprise_kpi_framework.md` and built into the relevant dbt mart

---

## 8. Open Items for Build Phase

- [ ] Confirm `mart_executive_kpi_daily` exists and is tested (dbt)
- [ ] Define target thresholds for each conditional-formatting flag with respective KPI owners
- [ ] Confirm BigQuery service account permissions for Looker Studio connector
- [ ] Validate comparison-period logic handles fiscal calendar (not just calendar month/quarter)
