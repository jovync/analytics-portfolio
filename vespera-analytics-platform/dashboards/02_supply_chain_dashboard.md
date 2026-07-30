# Supply Chain Dashboard — Looker Studio Design Specification

## Purpose

The Supply Chain Dashboard gives the VP of Supply Chain, Manufacturing Operations Director, and warehouse leads an operational view of inventory health, stock availability, procurement performance, and manufacturing quality. Where the Executive Dashboard summarizes one Supply Chain "pulse" tile, this dashboard is the full drill-down destination.

**Audience:** VP Supply Chain, Manufacturing Operations Director, Warehouse Managers, Procurement Leads
**Cadence:** Reviewed daily; inventory tiles refresh every 4 hours to match WMS↔e-commerce sync
**Governing principle:** All metrics trace to the Enterprise KPI Framework; all facts trace to `fact_inventory_daily`, `fact_manufacturing`, `fact_purchase_orders`, and `fact_returns`.

---

## 1. Data Source Strategy

| Looker Studio Data Source | Underlying dbt Mart | Grain | Refresh |
|---|---|---|---|
| `supply_inventory_daily` | `mart_inventory_summary` (built on `fact_inventory_daily`) | Date × Warehouse × Product | Every 4 hrs |
| `supply_stockout_summary` | `mart_stockout_summary` | Date × Warehouse × Category | Every 4 hrs |
| `supply_manufacturing_quality` | `mart_manufacturing_summary` (built on `fact_manufacturing`) | Batch × Supplier × Product | Hourly |
| `supply_procurement_performance` | `mart_purchase_order_summary` (built on `fact_purchase_orders`) | PO Line × Supplier × Warehouse | Daily |
| `supply_returns_disposition` | `mart_returns_summary` (built on `fact_returns`) | Date × Product × Warehouse | Near real-time |

**Freshness caveat to surface in the UI:** Inventory and stockout tiles should carry an "as of [last WMS sync]" caption — data can be up to 4 hours stale relative to the storefront. Manufacturing quality logs from third-party suppliers are noted as partially maintained, so any tile drawing on supplier-submitted QA data should include a small data-completeness indicator (e.g., % of batches with QA data received).

---

## 2. Report Structure (Pages)

```
Page 1 — Inventory Health Overview     (default landing page)
Page 2 — Stockout & Availability Detail
Page 3 — Manufacturing Quality
Page 4 — Procurement & Supplier Performance
Page 5 — Returns & Disposition
```

Persistent filter panel: date range, warehouse, product category, supplier — applies report-wide.

---

## 3. Page-by-Page Design

### Page 1 — Inventory Health Overview

Scorecards:

| Metric | Formula (per KPI Framework) | Owner |
|---|---|---|
| Inventory Turnover | COGS ÷ Average Inventory | VP Supply Chain |
| Stockout Rate | Stockout SKUs ÷ Active SKUs | VP Supply Chain |
| Inventory Valuation | Σ(quantity_on_hand × unit_cost_amount) | VP Supply Chain |
| Quantity in Transit | Σ quantity_in_transit | VP Supply Chain |

Below scorecards:
- Line chart: Inventory Valuation trend by day, split by Warehouse
- Bar chart: Quantity on Hand vs. Quantity Allocated by Warehouse (highlights over-allocation risk)
- "As of" freshness caption tied to WMS sync timestamp

### Page 2 — Stockout & Availability Detail

- Heat-map table: Stockout Rate by Warehouse × Product Category (conditional formatting red/yellow/green)
- Bar chart: Top 15 SKUs by days-out-of-stock in period
- Trend line: Stockout Rate over time, with target threshold reference line
- Table: SKUs currently at zero on-hand with quantity in transit and expected PO delivery date (from `fact_purchase_orders`)

### Page 3 — Manufacturing Quality

Scorecards:

| Metric | Formula | Owner |
|---|---|---|
| Manufacturing Defect Rate | Failed Units ÷ Produced Units | Production Manager |
| QA Pass Rate | QA Passed Units ÷ Produced Units | Production Manager |
| Unit Batch Cost | Total Batch Cost ÷ Produced Units | Production Manager |

- Bar chart: Defect Rate by Supplier
- Bar chart: Defect Rate by Product Category
- Table: Batches with defect rate above threshold, with `defect_reason_code` breakdown
- Data-completeness indicator: % of batches with supplier-submitted QA data present (addresses known third-party logging gaps)

### Page 4 — Procurement & Supplier Performance

- Scorecards: Average Lead Time (days), Purchase Price Variance, On-Time Delivery Rate (received_quantity vs. expected_delivery_date_key)
- Bar chart: Average Lead Time by Supplier
- Table: Supplier scorecard — Lead Time, PPV, Defect Rate, Quality Rating (`dim_supplier.quality_rating_score`) blended into one ranked view
- Scatter plot: Supplier Quality Rating vs. Defect Rate (identify suppliers whose scorecard rating doesn't match observed quality)

### Page 5 — Returns & Disposition

- Scorecard: Return Rate (Returned Units ÷ Sold Units)
- Bar chart: Return Rate by Product Category
- Stacked bar: Return disposition mix (Restock / Defective / Destroy) by Warehouse
- Table: Refund Amount and Restocking Fee by Warehouse

---

## 4. Calculated Fields (Looker Studio syntax)

```
Inventory Turnover (period):
SUM(cogs_amount) / AVG(inventory_valuation_amount)

Stockout Flag (SKU-day level):
CASE WHEN quantity_on_hand = 0 THEN 1 ELSE 0 END

Days of Supply:
quantity_on_hand / (SUM(units_sold_trailing_30d) / 30)

On-Time Delivery Flag:
CASE WHEN received_date <= expected_delivery_date THEN 1 ELSE 0 END

Data Completeness % (Manufacturing QA):
COUNT(batches_with_qa_data) / COUNT(total_batches)
```

---

## 5. Filters & Controls

| Control | Type | Applies To |
|---|---|---|
| Date Range | Date range control | All pages |
| Warehouse | Drop-down (multi-select) | Pages 1, 2, 5 |
| Product Category | Drop-down | Pages 1–3, 5 |
| Supplier | Drop-down | Pages 3, 4 |

---

## 6. Interactivity & Navigation

- Cross-filtering enabled within each page (click a warehouse bar → filters scorecards and tables on that page)
- Drill link back to Executive Dashboard's Supply Chain Pulse tile for context switching
- Table row click-through on Page 4 (Supplier Scorecard) to a filtered Page 3 view for that supplier's batch history

---

## 7. Visual & Governance Standards

- Same shared Looker Studio theme as the Executive Dashboard for brand consistency
- Chart titles use official KPI Framework names
- Every page footer shows: source mart name, last refresh timestamp, KPI Framework version
- No dashboard-local metric definitions — new metrics go through the KPI Framework first

---

## 8. Open Items for Build Phase

- [ ] Confirm `mart_inventory_summary` and `mart_manufacturing_summary` exist and pass dbt tests
- [ ] Define Stockout Rate and Defect Rate target thresholds with VP Supply Chain and Production Manager
- [ ] Decide whether Days of Supply becomes an official KPI Framework metric (currently dashboard-derived)
- [ ] Confirm data-completeness indicator logic for supplier-submitted QA logs
- [ ] Validate 4-hour refresh schedule aligns with Looker Studio's BigQuery extract/live-connection cache settings
