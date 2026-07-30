# KPI Framework ↔ Star Schema Reconciliation — DSO & CAC Gap Closure

## Purpose

Two Enterprise KPI Framework metrics — **Days Sales Outstanding (DSO)** and **Customer Acquisition Cost (CAC)** — reference source data that has no corresponding fact table in the current Star Schema Specification (`03_star_schema.md`). This document reconciles the two by proposing the minimum schema additions needed to make both KPIs buildable, following the same Kimball conventions already used for `fact_sales`, `fact_purchase_orders`, `fact_inventory_daily`, `fact_manufacturing`, and `fact_returns`.

This is a design proposal, not yet an approved schema change — see **Section 5** for open decisions that need a business owner's sign-off before implementation.

---

## 1. Gap Summary

| KPI | Framework Formula | Framework-Stated Source | Missing From Star Schema |
|---|---|---|---|
| DSO | Accounts Receivable ÷ Average Daily Credit Sales | NetSuite ERP | No fact table captures AR balances, aging, or credit terms |
| CAC | Marketing Spend ÷ New Customers | Meta, Google, TikTok, Shopify | No fact table captures ad platform spend; no attribution linkage from spend to acquired customer |

Both gaps share a root cause: the original data model was built primarily around **product movement** (sales, inventory, manufacturing, procurement, returns) — the physical goods lifecycle described in the Enterprise Systems Landscape. Financial receivables and marketing spend are **money-side** processes that were named in the KPI Framework but never modeled as facts.

---

## 2. Proposed Addition — Accounts Receivable (closes DSO)

### 2.1 New Fact: `fact_ar_aging_daily`

* **Business Owner:** Finance Manager
* **Technical Steward:** Analytics Engineering
* **Source System:** NetSuite ERP (AR Module)
* **Declared Grain:** One row per open customer invoice per calendar day (periodic snapshot)
* **Fact Table Type:** Periodic Snapshot Fact Table
* **Refresh Frequency:** Daily

**Keys:**
- `ar_snapshot_key` (Primary Key – Surrogate)
- `snapshot_date_key` (FK → `dim_date`)
- `customer_key` (FK → `dim_customer`)

**Degenerate Dimensions:** `invoice_number`, `payment_terms_code`

**Measures:**
- `invoice_amount` (Fully Additive Currency)
- `open_balance_amount` (Semi-Additive Currency — point-in-time balance, not summable across dates)
- `days_outstanding` (Non-Additive Integer — invoice age at snapshot date)
- `aging_bucket_0_30_amount` / `aging_bucket_31_60_amount` / `aging_bucket_61_90_amount` / `aging_bucket_90_plus_amount` (Semi-Additive Currency)

### 2.2 Star Schema Note — `fact_sales` Extension

DSO's denominator (Average Daily **Credit** Sales) requires distinguishing credit-term sales from immediate-payment sales. Rather than a new fact table, add one degenerate dimension to the existing `fact_sales`:

- `payment_terms_code` (Degenerate Dimension — e.g., `NET30`, `NET60`, `DUE_ON_RECEIPT`) — already partially implied by `payment_method`, but that field captures *how* payment was made, not *when it's due*. These are distinct concepts and both should be retained.

### 2.3 Resulting DSO Calculation

```
DSO = AVG(open_balance_amount from fact_ar_aging_daily, month-end snapshot)
      ÷ (SUM(net_revenue_amount) WHERE payment_terms_code != 'DUE_ON_RECEIPT' FROM fact_sales, trailing 30 days ÷ 30)
```

### 2.4 dbt Mart Impact

New mart: `mart_finance_ar_summary`, replacing the "Not yet built" placeholder in `finance_ar_dso` from the Finance Dashboard spec. Unblocks **Page 4 — Cash Collection (DSO)**.

---

## 3. Proposed Addition — Marketing Spend & Attribution (closes CAC)

### 3.1 New Dimension: `dim_campaign`

* **SCD Strategy:** Type 1 (campaign metadata rarely changes retroactively)
* **Key Attributes:**
  - `campaign_key` (Surrogate Primary Key)
  - `campaign_id` (Natural Key, platform-issued)
  - `campaign_name`, `marketing_platform` (Meta / Google / TikTok), `objective_type`
  - `start_date`, `end_date`

### 3.2 New Fact: `fact_marketing_spend`

* **Business Owner:** Marketing Director
* **Technical Steward:** Analytics Engineering
* **Source System:** Meta Ads API, Google Ads API, TikTok Ads API
* **Declared Grain:** One row per campaign per marketing platform per calendar day
* **Fact Table Type:** Transaction Fact Table
* **Refresh Frequency:** Daily

**Keys:**
- `marketing_spend_key` (Primary Key – Surrogate)
- `spend_date_key` (FK → `dim_date`)
- `campaign_key` (FK → `dim_campaign`)

**Measures:**
- `spend_amount` (Fully Additive Currency)
- `impressions_count` (Fully Additive Integer)
- `clicks_count` (Fully Additive Integer)
- `platform_reported_conversions_count` (Fully Additive Integer — kept for reconciliation against first-party attribution, not used as the CAC source of truth)

### 3.3 Attribution Linkage — the Real Modeling Decision

Spend data alone doesn't produce CAC — it has to be connected to *which customers that spend acquired*. This is the part that's a genuine business decision, not just a pipeline task. Three options, in increasing complexity:

| Option | Description | Effort | Accuracy |
|---|---|---|---|
| **A. Platform-reported conversions** | Trust Meta/Google/TikTok's own conversion counts (`platform_reported_conversions_count`) as "new customers" | Low | Low — platforms over-count due to overlapping attribution windows |
| **B. First-touch attribution (recommended)** | Extend `dim_customer` with `acquisition_campaign_key` (FK → `dim_campaign`), set at the customer's first-ever order, sourced from UTM/click-tracking captured at signup | Medium | Good — matches the existing `acquisition_channel_name` attribute already in `dim_customer`, just adds campaign-level granularity |
| **C. Multi-touch attribution fact** | New bridge fact at (customer, campaign, touchpoint) grain with attribution-weight measure, requires a touchpoint-level clickstream source not currently in the Systems Landscape | High | Best, but out of scope until clickstream capture exists |

**Recommendation: Option B.** It reuses the acquisition-channel pattern `dim_customer` already has, requires no new fact table beyond `fact_marketing_spend`, and matches the KPI Framework's own "Daily by Campaign" reporting grain for CAC without over-building. Option C stays a documented future enhancement rather than a blocker.

### 3.4 Resulting CAC Calculation (Option B)

```
CAC = SUM(spend_amount FROM fact_marketing_spend, by campaign_key)
      ÷ COUNT(DISTINCT customer_key FROM dim_customer WHERE acquisition_campaign_key = campaign_key AND acquisition_date IN period)
```

### 3.5 dbt Mart Impact

New mart: `mart_marketing_spend_cac`, replacing the "Not yet built" placeholder in `marketing_spend_cac` from the Marketing Dashboard spec. Unblocks **Page 3 — Acquisition Cost & Efficiency** and **Page 4 — Campaign-Level Performance**.

---

## 4. Documentation Updates Required

| Document | Update Needed |
|---|---|
| `03_star_schema.md` | Add `fact_ar_aging_daily`, `fact_marketing_spend`, `dim_campaign` specifications (Section 2 and 3 above, in existing format) |
| `04_physical_erd.md` | Add DDL and relationship lines for the two new facts and one new dimension |
| `05_data_dictionary.md` | Add column-level dictionary entries matching the pattern used for existing facts (Section 4.x) |
| `02_logical_data_model.md` | Add `INVOICE` and `CAMPAIGN` as new logical entities with their mapping to the new dimensional tables |
| `05_enterprise_kpi_framework.md` | Update "Enterprise Data Model Impact" notes for DSO and CAC to reference the now-concrete fact tables instead of a generic source-system name |

---

## 5. Open Decisions Requiring Business Sign-Off

- [ ] **DSO applicability:** Confirm with Head of Finance whether Vespera's revenue is materially credit-term (B2B/wholesale) vs. point-of-sale (retail/e-commerce). If credit sales are a small minority, DSO may need to be rescoped to wholesale accounts only, or reconsidered as an enterprise-wide KPI.
- [ ] **Attribution model:** Confirm Option B (first-touch, single attribution at `dim_customer` level) with Marketing Director as sufficient, vs. requiring multi-touch (Option C) — this changes both engineering scope and how campaign performance conversations happen.
- [ ] **`payment_terms_code` backfill:** Confirm NetSuite actually distinguishes credit terms at the order level in a way that can populate this field on historical `fact_sales` records, or whether it's only available going forward.
- [ ] **AR snapshot cadence:** Daily grain proposed above for `fact_ar_aging_daily`, but KPI Framework states DSO is reported monthly — confirm daily grain is worth the extra pipeline cost vs. a simpler month-end-only snapshot.

---

## 6. Summary

Both gaps stem from the same pattern: the KPI Framework named a metric and its source system before the corresponding fact table existed, which is expected in a business-first design process — the KPI Framework is supposed to drive the data model, not the other way around (see `05_enterprise_kpi_framework.md`, Section "Relationship to the Enterprise Data Model"). This document closes the loop for DSO and CAC specifically. Once Section 5's open decisions are resolved, `03_star_schema.md`, `04_physical_erd.md`, and `05_data_dictionary.md` should be updated per Section 4, and the two new dbt marts built to unblock the Finance and Marketing dashboard pages that are currently marked "Pending Data Source."

---

## Resolution Status (as of dbt implementation)

The schema additions proposed above were implemented as of the v1.2 documentation updates to `02_logical_data_model.md`, `03_star_schema.md`, `04_physical_erd.md`, and `05_data_dictionary.md`. Marketing spend / CAC (Section 3) is now built and tested end-to-end in dbt (`stg_marketing_spend` → `dim_campaign` → `fact_marketing_spend`, 15/15 tests passing). AR aging / DSO (Section 2) is generated at the Python source layer (`ar_invoices.py`) but the `fact_ar_aging_daily` dbt model itself is not yet built — still pending as of this checkpoint.

One implementation deviation from this memo worth noting: `dim_campaign`'s `objective_type` attribute (Section 3.1) was not carried through to the actual build, since the real `marketing_spend.py` generator doesn't produce that field. `03_star_schema.md` and `05_data_dictionary.md` still need a follow-up correction to drop or mark it unsourced.