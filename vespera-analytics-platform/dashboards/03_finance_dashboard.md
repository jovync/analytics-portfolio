# Finance Dashboard — Looker Studio Design Specification

## Purpose

The Finance Dashboard gives the Head of Finance and Finance Manager a governed view of revenue quality, profitability, and cash collection performance. It's the audit-grade companion to the Executive Dashboard's top-line Profitability page — same numbers, full traceability to line-item detail.

**Audience:** Head of Finance, Finance Manager, Controller
**Cadence:** Daily for revenue/margin; monthly for DSO (matches KPI Framework reporting grain)
**Governing principle:** All metrics trace to the Enterprise KPI Framework. Margin and revenue trace to `fact_sales` and `fact_returns`; DSO now traces to `fact_ar_aging_daily`, added in the v1.2 schema reconciliation (see `06_kpi_schema_reconciliation.md`). **Page 4 is unblocked as of this update** — Section 6 below records the resolved gap for traceability rather than as an open blocker.

---

## 1. Data Source Strategy

| Looker Studio Data Source | Underlying dbt Mart | Grain | Refresh |
|---|---|---|---|
| `finance_revenue_daily` | `mart_finance_summary` (built on `fact_sales`) | Date × Channel × Product | Daily |
| `finance_margin_summary` | `mart_finance_summary` | Date × Product Category × Channel | Daily |
| `finance_returns_impact` | `mart_returns_summary` (built on `fact_returns`) | Date × Product × Channel | Near real-time |
| `finance_ar_dso` | `mart_finance_ar_summary` (built on `fact_ar_aging_daily` + `fact_sales.payment_terms_code`) | Month × Customer/Account | Daily snapshot, monthly reported |

**Freshness caveat:** Marketplace revenue (Shopee/Lazada) is reconciled at month-end close per the systems landscape, so month-to-date marketplace figures on this dashboard should be visually flagged as **preliminary / unreconciled** until close completes — a hard rule for a finance-facing tool where numbers get quoted externally.

---

## 2. Report Structure (Pages)

```
Page 1 — Revenue & Margin Overview     (default landing page)
Page 2 — Profitability by Segment
Page 3 — Returns & Margin Erosion
Page 4 — Cash Collection (DSO)
Page 5 — Marketplace Reconciliation Status
```

Persistent filter panel: date range (with fiscal calendar toggle), channel, product category, region — applies report-wide.

---

## 3. Page-by-Page Design

### Page 1 — Revenue & Margin Overview

Scorecards:

| Metric | Formula (per KPI Framework) | Owner |
|---|---|---|
| Net Revenue | Gross Sales − Discounts − Returns − Taxes | Head of Finance |
| Gross Margin % | (Net Revenue − COGS) ÷ Net Revenue | Head of Finance |
| COGS | Σ cogs_amount | Head of Finance |
| Discount Amount | Σ discount_amount | Head of Finance |

- Combo chart: Net Revenue (bar) vs. Gross Margin % (line), daily, last 90 days
- Waterfall chart: Gross Sales → Discounts → Returns → Taxes → Net Revenue (makes the KPI Framework's exact formula visible, not just the end number)
- Comparison toggle: this period vs. prior period, this period vs. same period last fiscal year

### Page 2 — Profitability by Segment

- Bar chart: Gross Margin % by Product Category
- Bar chart: Gross Margin % by Sales Channel (Shopify Plus, Shopify POS, Shopee/Lazada)
- Geo map: Net Revenue and Gross Margin % by Country
- Table: Margin by Product Category × Channel matrix, conditional formatting vs. target

### Page 3 — Returns & Margin Erosion

- Scorecard: Return Rate, Total Refunded Amount, Total Restocking Fee Collected
- Bar chart: Refunded Amount by Product Category
- Line chart: Return Rate trend with target reference line
- Table: Top 10 SKUs by margin erosion from returns (Refunded Amount − Restocking Fee, ranked descending)

### Page 4 — Cash Collection (DSO)

Scorecards:

| Metric | Formula (per KPI Framework) | Owner |
|---|---|---|
| DSO | AVG(open_balance_amount) ÷ (Trailing 30-day Credit Net Revenue ÷ 30) | Finance Manager |
| Total Open AR Balance | Σ open_balance_amount (latest snapshot) | Finance Manager |
| Invoices 90+ Days Past Due | Count of invoices where `aging_bucket_90_plus_amount` > 0 | Finance Manager |

- Line chart: DSO trend by month, with target reference line
- Stacked bar chart: AR aging composition (0–30 / 31–60 / 61–90 / 90+ days) by month, sourced from `fact_ar_aging_daily`'s four aging bucket measures
- Table: Top 15 accounts by open balance, sorted descending, with `days_outstanding` and `payment_terms_code` columns for collections triage
- Scorecard note: DSO's denominator excludes `DUE_ON_RECEIPT` transactions (per `fact_sales.payment_terms_code`) so point-of-sale revenue doesn't dilute the credit-collection metric

**Scoping caveat carried over from reconciliation:** if credit-term sales turn out to be a small share of total revenue, DSO here should be read as a wholesale/B2B-specific metric rather than an enterprise-wide one — this is still an open question with Head of Finance (see Section 6).

### Page 5 — Marketplace Reconciliation Status

- Table: Marketplace revenue by platform (Shopee, Lazada) — Preliminary (pre-close) vs. Reconciled (post-close) side by side
- Status indicator per platform: Reconciled / Pending / Variance Flagged
- Variance chart: Preliminary vs. Reconciled revenue delta by month, to track how often and by how much marketplace estimates move at close

---

## 4. Calculated Fields (Looker Studio syntax)

```
Gross Margin %:
(SUM(net_revenue_amount) - SUM(cogs_amount)) / SUM(net_revenue_amount)

Net Revenue (waterfall step):
SUM(gross_revenue_amount) - SUM(discount_amount) - SUM(refunded_amount) - SUM(tax_amount)

Margin Erosion from Returns:
SUM(refunded_amount) - SUM(restocking_fee_amount)

DSO (period):
AVG(open_balance_amount) / (SUM(net_revenue_amount) FILTER (payment_terms_code != "DUE_ON_RECEIPT") / 30)

AR Aging Status Flag:
CASE
  WHEN aging_bucket_90_plus_amount > 0 THEN "⚠ 90+ Days Past Due"
  WHEN aging_bucket_61_90_amount > 0 THEN "⏳ 61-90 Days"
  ELSE "✅ Current"
END

Reconciliation Variance %:
(SUM(reconciled_revenue) - SUM(preliminary_revenue)) / SUM(preliminary_revenue)

Marketplace Data Status Flag:
CASE
  WHEN reconciliation_status = "Reconciled" THEN "✅ Final"
  WHEN reconciliation_status = "Pending" THEN "⏳ Preliminary"
  ELSE "⚠ Variance Flagged"
END
```

---

## 5. Filters & Controls

| Control | Type | Applies To |
|---|---|---|
| Date Range (with fiscal toggle) | Date range control | All pages |
| Sales Channel | Drop-down (multi-select) | Pages 1–3 |
| Product Category | Drop-down | Pages 1–3 |
| Region/Country | Drop-down | Pages 1, 2 |
| Customer/Account | Drop-down (search-enabled) | Page 4 |
| Marketplace Platform | Drop-down | Page 5 |

---

## 6. Resolved Data Gap — DSO / Accounts Receivable *(Closed in v1.2 schema reconciliation)*

The KPI Framework defines DSO as `Accounts Receivable ÷ Average Daily Credit Sales`, owned by the Finance Manager and sourced from NetSuite ERP. The original star schema had no fact table capturing AR balances or credit sales terms — `fact_sales` captured revenue recognition at the order line-item level but not receivables aging or payment terms.

**This was closed via schema reconciliation** (`06_kpi_schema_reconciliation.md`):
1. New **`fact_ar_aging_daily`** periodic snapshot (grain: Customer × Day), sourced from NetSuite AR ledger — see `03_star_schema.md` Section 6.6.
2. New **`payment_terms_code`** degenerate dimension added to `fact_sales`, distinguishing credit-term sales from point-of-sale for DSO's denominator.

**Still open, not a data gap but a scoping question:** whether DSO is a meaningful enterprise-wide KPI for Vespera given its revenue mix looks predominantly point-of-sale rather than credit-terms. This is a business decision for Head of Finance, not an engineering blocker — Page 4 is buildable regardless, but its interpretation may need scoping down to wholesale/B2B accounts once that's answered.

---

## 7. Interactivity & Navigation

- Cross-filtering enabled within each page
- Drill link back to Executive Dashboard's Profitability page
- Waterfall chart (Page 1) links to Page 3 (Returns) when clicking the "Returns" segment, for margin erosion root-cause

---

## 8. Visual & Governance Standards

- Same shared Looker Studio theme as Executive and Supply Chain dashboards
- Chart titles use official KPI Framework names
- **Unreconciled marketplace figures must always carry a visible "Preliminary" badge** — this is a finance-facing tool and silently blending estimated and reconciled revenue would undermine trust in the single-source-of-truth principle
- Every page footer shows: source mart name, last refresh timestamp, KPI Framework version

---

## 9. Open Items for Build Phase

- [ ] Confirm `mart_finance_summary`, `mart_returns_summary`, and `mart_finance_ar_summary` exist and pass dbt tests
- [ ] Define Gross Margin % target thresholds per Product Category with Head of Finance
- [ ] Define DSO target threshold with Finance Manager (for the trend line reference)
- [ ] Confirm fiscal calendar mapping in `dim_date` is wired into the date range comparison control
- [ ] Validate marketplace reconciliation status field is populated correctly post month-end close
- [ ] **Resolve DSO scoping question** (Section 6) with Head of Finance — enterprise-wide vs. wholesale/B2B-only interpretation
- [ ] Confirm NetSuite can backfill `payment_terms_code` on historical `fact_sales` records, or whether Page 4 comparisons should start from the field's go-live date