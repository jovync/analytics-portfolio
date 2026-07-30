# ETL Design

**Project:** Vespera Lifestyle Analytics Platform
**Status:** Extract, Load, and Transform (staging + intermediate + mart layers) complete — dashboard phase next
**Last Updated:** 2026-07-30

---

## 1. Purpose

This document describes the end-to-end data pipeline architecture
for the Vespera Analytics Platform: how data is generated,
extracted, loaded, and transformed into the enterprise dimensional
model that powers Looker Studio dashboards.

---

## 2. Pipeline Overview
Python Synthetic Data Generators
│
▼
Raw CSV Files (data/raw/)
│
▼
BigQuery Raw Dataset (vespera_dw_raw)
│
▼
dbt Staging Models (stg_*) — vespera_dw_staging
│
▼
dbt Intermediate Models (int_*) — vespera_dw_intermediate
│
▼
dbt Mart Models (dim_*, fact_*) — vespera_dw
│
▼
Looker Studio Dashboards

This mirrors the KPI Governance Workflow defined in the Enterprise
KPI Framework (`docs/01_business/05_enterprise_kpi_framework.md`).

---

## 3. Stage 1 — Extract / Generate (Complete)

### Source
In place of live operational systems (NetSuite ERP, Shopify, WMS,
etc. — see Enterprise Systems Landscape), this project uses a
custom Python simulation engine to generate relationally-consistent
synthetic data standing in for those systems.

### Location
`python/generators/` — 13 generator modules, orchestrated by
`python/generate_data.py`.

### Generators & Dependency Order

| Order | Generator | Depends On | Output Table |
|---|---|---|---|
| 1 | `suppliers.py` | — | `suppliers.csv` |
| 2 | `products.py` | suppliers | `products.csv` |
| 3 | `customers.py` | — | `customers.csv` |
| 4 | `warehouses.py` | — | `warehouses.csv` |
| 5 | `marketing_spend.py` | — | `marketing_spend.csv` |
| 6 | `assignment.py` | products, warehouses | `warehouse_product_assignment.csv` |
| 7 | `inventory_snapshot.py` | products, warehouses, assignment | `inventory_snapshot.csv` |
| 8 | `purchase_orders.py` | products, suppliers, warehouses, assignment | `purchase_orders.csv` |
| 9 | `orders.py` | customers, warehouses | `orders.csv` |
| 10 | `order_items.py` | orders, products, assignment, warehouses | `order_items.csv` |
| 11 | `shipments.py` | orders, customers, warehouses | `shipments.csv` |
| 12 | `returns.py` | shipments, order_items, products | `returns.csv` |
| 13 | `inventory_movements.py` | orders, order_items, returns, purchase_orders | `inventory_movements.csv` |

### Output Volume (original generation run)

| Table | Row Count |
|---|---:|
| Suppliers | 30 |
| Products | 1,200 |
| Customers | 10,000 |
| Warehouses | 7 |
| Warehouse-Product Assignment | 4,756 |
| Inventory Snapshot | 4,016 |
| Purchase Orders | 142,057 |
| Orders | 50,000 |
| Order Items | 94,127 |
| Shipments | 40,057 |
| Returns | 3,611 |
| Inventory Movements | 192,199 |
| Marketing Spend | 678 |
| **Total** | **~542,700 rows** |

> **Note:** The catalog was regenerated after the `reorder_quantity`
> fix described in §7 below. Fixed-target counts (Suppliers,
> Products, Customers, Warehouses) are unchanged since those come
> from `NUM_*` constants in `config.py`, not randomness. Variable
> counts have shifted somewhat — confirmed via dbt build output that
> Inventory Movements is now ~195,700 rows (was 192,199) — but this
> table hasn't been fully re-tallied against the current data. Treat
> the fixed-target rows as authoritative and the variable ones as
> approximate until refreshed.

### Reproducibility
Fixed random seed (`RANDOM_SEED = 42`, `config.py`), applied
independently within each generator function. Re-running
`generate_data.py` produces identical output **for a given version
of the generator code** — changing any generator's internal logic
(e.g. adding or removing a `random.*` call) shifts that function's
entire draw sequence, which cascades into every value drawn
afterward. This is expected, seeded-random behavior, not a
reproducibility bug — see §7 for a real example.

### Known Limitations
See `00_data_generation_assumptions.md` for the full list of
deliberate simplifications made in this layer.

---

## 4. Stage 2 — Load to BigQuery (Complete)

### Target
- **Project:** `vespera-analytics-platform`
- **Dataset:** `vespera_dw_raw`
- **Region:** `asia-southeast1` (Singapore)

### Load Method
**Decision:** Python client (`google-cloud-bigquery`), scripted in
`python/load_to_bigquery.py`, looping over `data/raw/*.csv`. Chosen
over the `bq` CLI or manual console upload for the same reason the
rest of the pipeline is Python — one reproducible, version-controlled
script rather than a manual step someone has to remember to repeat
correctly.

### Schema Handling
Each table loads with `WRITE_TRUNCATE`, so re-running the script is
idempotent — every run fully replaces the table rather than
appending duplicates. No transformation or cleaning happens at this
stage — raw load only, consistent with an ELT (not ETL) pattern. All
business logic and cleaning happens in dbt (Stage 3).

Schema is `autodetect=True` with `skip_leading_rows=1` for most
tables — **with one deliberate exception.** `raw_warehouses` and
`raw_warehouse_product_assignment` are given an **explicit schema**
instead. BigQuery's autodetect determines whether row 1 is a header
by checking whether its column types look different from the data
rows; when every column in a table is `STRING` typed (true for both
of these — no numeric or date column to create type contrast),
autodetect can fail to recognize a header row at all and silently
loads with placeholder names like `string_field_0`. This was caught
via `dbt run` failing with `Unrecognized name: warehouse_id` and
diagnosed by checking `INFORMATION_SCHEMA.COLUMNS` directly. Explicit
schema sidesteps the autodetect heuristic entirely, so it can't
recur, including on future full regenerations.

### Partitioning & Clustering
**Not yet implemented**, for either the raw tables or the dbt mart
tables — a deliberate deferral, not an oversight. `04_physical_erd.md`
specifies a partitioning/clustering strategy for the mart-layer fact
tables, but at current data volumes (largest table ~2.9M rows,
`fact_inventory_daily`) an unpartitioned BigQuery table scans fast
enough that the added complexity isn't paying for itself yet. Worth
revisiting if either (a) the dataset grows meaningfully, or (b)
Looker Studio dashboard query patterns reveal a specific column
that's filtered on constantly enough to justify partitioning around
it.

| Table | Partition Column (planned) | Cluster Columns (planned) |
|---|---|---|
| `fact_sales` | `order_date_key` (via `dim_date`) | `warehouse_key`, `product_key` |
| `fact_purchase_orders` | `po_date_key` | `supplier_key`, `product_key` |
| `fact_inventory_daily` | `snapshot_date_key` | `warehouse_key`, `product_key` |
| `fact_returns` | `return_date_key` | `warehouse_key`, `product_key` |

---

## 5. Stage 3 — Transform with dbt (Complete)

See `02_dbt_transformation_spec.md` for the full model-by-model
specification.

Implemented layers:
- **Staging (`stg_*`):** 13 models, one per raw table, views in
  `vespera_dw_staging`. Light cleaning, casting, renaming to
  enterprise naming standards.
- **Intermediate (`int_*`):** 3 models in `vespera_dw_intermediate`,
  supporting the `fact_inventory_daily` derivation specifically —
  running ledger totals, snapshot calibration offset, and a bounded
  daily calendar spine.
- **Marts (`dim_*`, `fact_*`):** 5 dimensions + 4 facts, tables in
  `vespera_dw`, per the Star Schema Architectural Specification
  (`docs/02_architecture/03_star_schema.md`).
- **Data quality tests:** 91 dbt data tests across all layers — see
  `03_data_quality_framework.md` for the full inventory and
  methodology.

---

## 6. Stage 4 — Dashboards (Planned)

Looker Studio, connected to BigQuery mart tables (never raw or
staging tables). Build order per project overview: Executive →
Supply Chain → Finance → Marketing.

---

## 7. Case Study: A Data Quality Issue Caught After "Done"

Worth documenting here rather than only in a commit message, since
it's a good example of why manual spot-checks against ground truth
still matter even after every automated test passes.

**What happened:** After `fact_inventory_daily` passed all
referential-integrity and uniqueness tests, a manual review of its
output (checking one warehouse/product pair's day-by-day balance by
hand) surfaced a purchase order receipt of 4,500 units for a product
selling ~4-9 units/day — three-plus years of supply in one order.
Investigating further showed this wasn't a one-off: every
Distribution-Center-fulfilled product ordered the exact same
quantity on every single purchase order it ever generated, and large
groups of unrelated products shared identical order quantities
(e.g. 18 different products all ordering exactly 1,600 units).

**Root cause:** `products.py` assigned `reorder_quantity` via
`random.choice([250, 500, 1000])` — completely independent of the
product's actual `popularity_weight`. `purchase_orders.py` then
multiplied that arbitrary base by a demand-tier multiplier, scaling
an already-disconnected number rather than a demand-linked one.

**Fix:** `reorder_quantity` is now derived from `popularity_weight`'s
percentile rank (continuous, not tiered) plus per-product jitter, and
the redundant demand-tier multiplier was removed for
Distribution-Center orders (kept for Retail Store orders, whose base
quantity is still an independent random draw). Verified afterward:
max products sharing an identical order quantity dropped from 18+ to
≤6 (plausible coincidence at 1,200 products), and mean order quantity
now increases monotonically by demand tier (Low 274 → Medium 518 →
High 534 → Very High 771).

**Takeaway:** All the dbt tests that matter for structural integrity
(uniqueness, referential integrity, accepted values) passed
throughout this entire episode — they were never wrong. This class of
issue — plausible-looking values that are individually valid but
collectively nonsensical — isn't something uniqueness/not-null/
relationship tests are designed to catch. See
`03_data_quality_framework.md` §6 for how this changed the testing
approach going forward.

---

## 8. Pipeline Status Checklist

- [x] Python generator layer (13 generators + orchestrator)
- [x] Data generation assumptions documented
- [x] BigQuery raw dataset created and loaded
- [ ] Partitioning/clustering applied (deliberately deferred — §4)
- [x] dbt project scaffolded
- [x] dbt staging models (13/13)
- [x] dbt intermediate models (3/3)
- [x] dbt mart models — dimensions (5/5)
- [x] dbt mart models — facts (4/4)
- [x] dbt data quality tests (91 tests, all passing)
- [ ] Looker Studio dashboards