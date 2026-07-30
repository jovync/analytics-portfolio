# dbt Transformation Specification

**Project:** Vespera Lifestyle Analytics Platform
**Status:** Staging, intermediate, and mart layers complete
**Last Updated:** 2026-07-30

---

## 1. Purpose

This document specifies the dbt project that transforms
`vespera_dw_raw` into the enterprise dimensional model. It covers
project structure, layering conventions, every model's purpose and
grain, and the handful of places where this implementation
deliberately diverges from the aspirational architecture in
`04_physical_erd.md` — with the reasoning for each divergence stated
explicitly, so a future reader doesn't mistake a considered decision
for an oversight.

---

## 2. Project Structure

```
vespera_dw/
  dbt_project.yml
  packages.yml              (dbt_utils)
  models/
    staging/
      _vespera__sources.yml
      _vespera__staging_models.yml
      stg_suppliers.sql
      stg_products.sql
      stg_customers.sql
      stg_warehouses.sql
      stg_warehouse_product_assignment.sql
      stg_inventory_snapshot.sql
      stg_purchase_orders.sql
      stg_orders.sql
      stg_order_items.sql
      stg_shipments.sql
      stg_returns.sql
      stg_inventory_movements.sql
      stg_marketing_spend.sql
    intermediate/
      _vespera__intermediate.yml
      int_inventory_movement_running_totals.sql
      int_inventory_balance_offset.sql
      int_inventory_daily_spine.sql
    marts/
      core/
        _vespera__marts_core.yml
        dim_date.sql
        dim_product.sql
        dim_customer.sql
        dim_warehouse.sql
        dim_supplier.sql
        fact_sales.sql
        fact_purchase_orders.sql
        fact_returns.sql
        fact_inventory_daily.sql
```

---

## 3. Dataset Strategy

| Layer | Dataset | Materialization |
|---|---|---|
| Raw | `vespera_dw_raw` | Tables (loaded by Python, not dbt) |
| Staging | `vespera_dw_staging` | Views |
| Intermediate | `vespera_dw_intermediate` | Views, except `int_inventory_movement_running_totals` (table — see §5) |
| Marts | `vespera_dw` | Tables |

**Divergence from `04_physical_erd.md`:** that document specifies a
five-dataset architecture (`vespera_raw` → `vespera_staging` →
`vespera_intermediate` → `vespera_dw` → `vespera_reporting`) under a
project named `vespera-analytics-prod`. The actual implementation
uses four datasets under the real project (`vespera-analytics-platform`),
folding "reporting" into the mart layer directly (no separate
BI-optimized semantic view layer) since Looker Studio can query
`vespera_dw`'s fact/dim tables directly at this project's scale — a
fifth layer of pre-aggregated views isn't earning its complexity yet.
Dataset naming also follows the pattern the raw layer already
established (`vespera_dw_raw`, `vespera_dw_staging`, etc.) rather
than the ERD's flatter `vespera_raw`/`vespera_staging` naming, for
consistency with what was already live before dbt was scaffolded.

---

## 4. Staging Layer

One model per raw table, 1:1 grain, light cleaning only (trimming,
casing, renaming to consistent snake_case, basic type casting). No
joins, no business logic — that's what the intermediate/mart layers
are for.

| Model | Source | Notes |
|---|---|---|
| `stg_suppliers` | `raw_suppliers` | |
| `stg_products` | `raw_products` | Adds `is_currently_sellable` (derived from `lifecycle_status` + `launch_date`) |
| `stg_customers` | `raw_customers` | |
| `stg_warehouses` | `raw_warehouses` | Single conformed location table — DC, Retail Store, Returns Center. See `03_star_schema.md` §7.4 for why there's no separate store staging model. |
| `stg_warehouse_product_assignment` | `raw_warehouse_product_assignment` | Bridge table — shared source of truth for "does this warehouse carry this product," consumed by `inventory_snapshot`, `purchase_orders`, and `order_items` generators alike |
| `stg_inventory_snapshot` | `raw_inventory_snapshot` | |
| `stg_purchase_orders` | `raw_purchase_orders` | |
| `stg_orders` | `raw_orders` | |
| `stg_order_items` | `raw_order_items` | |
| `stg_shipments` | `raw_shipments` | `SELECT *` pass-through — not yet tightened to explicit/cast columns (full schema not independently verified column-by-column; ran clean regardless) |
| `stg_returns` | `raw_returns` | `refunded_amount`/`restocking_fee_amount` deliberately **excluded** — confirmed absent from source. See §6. |
| `stg_inventory_movements` | `raw_inventory_movements` | `SELECT *` pass-through, same rationale as `stg_shipments` |
| `stg_marketing_spend` | `raw_marketing_spend` | `SELECT *` pass-through, same rationale |

---

## 5. Intermediate Layer

Exists for exactly one purpose: deriving `fact_inventory_daily`,
which isn't a direct 1:1 mirror of any raw table. `raw_inventory_snapshot`
is a single point-in-time reading per (warehouse, product); a real
daily balance has to be reconstructed from that snapshot plus the
signed movement ledger.

| Model | Grain | Purpose |
|---|---|---|
| `int_inventory_movement_running_totals` | One row per movement event | Running cumulative signed-quantity total per (warehouse, product), via window function. Materialized as a **table**, not the layer's default view — this window function over ~195K rows is the expensive step in the whole chain and shouldn't recompute on every downstream reference. |
| `int_inventory_balance_offset` | One row per (warehouse, product) in the snapshot | Calibration offset anchoring the ledger's running total to the one real balance available: `opening_balance_offset = snapshot.quantity_on_hand − cumulative_ledger_change_as_of(snapshot_date)`. |
| `int_inventory_daily_spine` | One row per (warehouse, product, day) | Daily calendar grid, bounded to each product's active lifecycle window intersected with the simulation period (2024-01-01 to 2025-12-31) — not a blind cross join, to keep row count sane and avoid meaningless pre-launch/post-discontinuation rows. |

Full derivation logic, including the forward-fill approach for days
with no movement activity, is documented in `fact_inventory_daily.sql`'s
header comment and was manually verified against a real
(warehouse, product) pair's day-by-day balance — see §7 for the
verification method.

---

## 6. Mart Layer

### 6.1 Dimensions

All five are **SCD Type 1** (current-state only, overwrite on
change), each with a reserved unknown-member row (`*_key = -1`) so
fact table joins never silently drop a row on a missing foreign key.
Surrogate keys via `FARM_FINGERPRINT()` on the natural key.

| Dimension | Natural Key | Row Count | Notes |
|---|---|---:|---|
| `dim_date` | `full_date` | ~1,461 | Generated calendar spine (2023-01-01 to 2026-12-31), no source table. Fiscal year assumed = calendar year (no evidence otherwise anywhere in source docs). `holiday_flag` is a simplified heuristic, not a real per-country public holiday calendar. |
| `dim_product` | `product_id` | 1,201 (incl. unknown) | |
| `dim_customer` | `customer_id` | 10,001 (incl. unknown) | |
| `dim_warehouse` | `warehouse_id` | 8 (incl. unknown) | Single conformed location dimension — no `dim_store` |
| `dim_supplier` | `supplier_id` | 31 (incl. unknown) | |

**SCD Type 2 deferred, not abandoned.** `03_star_schema.md` specifies
Type 2 for `dim_product` and `dim_customer`. The raw data is a single
point-in-time generation, not a real change stream — there's no
historical change data to actually track yet, so implementing full
Type 2 mechanics now would be tracking history that doesn't exist.
Revisit with `dbt snapshot` if/when this pipeline runs on a recurring
schedule against a source that genuinely changes over time.

### 6.2 Facts

| Fact | Grain | Row Count | Notes |
|---|---|---:|---|
| `fact_sales` | One row per order line item | ~94K | |
| `fact_purchase_orders` | One row per purchase order | ~142K | Each raw row is already atomic — no separate PO-header-vs-line split in this source |
| `fact_returns` | One row per returned order line item | ~3.6K | `refunded_amount`/`restocking_fee_amount` **derived** here — see §6.3 |
| `fact_inventory_daily` | One row per (warehouse, product, day) | ~2.9M | See §5 for derivation |

`fact_manufacturing` and `dim_promotion`, both specified in
`03_star_schema.md`, are **out of scope** — no manufacturing batch or
promotion/discount-campaign source data exists anywhere in the raw
layer (`raw_marketing_spend` captures channel-level ad spend, not
order-level promotions). Not built here; reintroduce only if a future
data-generation pass adds real source tables for either.

### 6.3 Derived Measures — `fact_returns`

`refunded_amount` and `restocking_fee_amount` are documented in
`03_star_schema.md`/`05_data_dictionary.md` as if they're raw source
columns. They aren't — confirmed absent from `raw_returns` via
`INFORMATION_SCHEMA.COLUMNS`. Rather than ship the fact table without
them, they're **derived in `fact_returns.sql` itself**:

- `refunded_amount` = returned quantity × the original order line
  item's actual net unit price (prorated)
- `restocking_fee_amount` = 10% of that, only when
  `return_reason = 'Customer Remorse'`

This follows the business logic already described (but not
implemented) in `00_data_generation_assumptions.md`. **Open item:**
`03_star_schema.md` and `05_data_dictionary.md` should be updated to
note these are mart-layer derived measures, not raw source columns —
not yet done as of this document's last update.

---

## 7. Verification Methodology

Every model's row count and referential integrity is covered by dbt
tests (see `03_data_quality_framework.md`), but `fact_inventory_daily`
specifically — the most logic-heavy model in the project — was also
manually spot-checked against ground truth before being considered
done:

1. Picked a real (warehouse, product) pair with meaningful movement
   activity from `raw_inventory_movements`.
2. Pulled its `raw_inventory_snapshot` row directly.
3. Queried `fact_inventory_daily` for that same pair around the
   snapshot date.
4. Confirmed `quantity_on_hand` in the fact matched the raw snapshot
   **exactly** on the snapshot date (validates the calibration offset
   math), and that day-to-day deltas matched `units_sold_qty`/
   `units_returned_qty`/`units_received_qty` exactly on every single
   day checked (validates the running-total and forward-fill logic).

This caught nothing wrong with the derivation itself, but the same
manual-inspection habit is what caught the `reorder_quantity` data
quality issue documented in `01_etl_design.md` §7 — worth keeping as
standard practice for any model built on derived/computed logic,
not just ones that fail tests.

---

## 8. Build & Test Commands

```bash
# Full rebuild
dbt run
dbt test

# By layer
dbt run --select staging
dbt run --select intermediate
dbt run --select marts.core

# Single model + its tests
dbt run --select fact_inventory_daily
dbt test --select fact_inventory_daily
```