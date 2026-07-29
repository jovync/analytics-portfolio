# ETL Design

**Project:** Vespera Lifestyle Analytics Platform
**Status:** Extract/Generate phase complete — Load & Transform phases in progress
**Last Updated:** [fill in date]

---

## 1. Purpose

This document describes the end-to-end data pipeline architecture
for the Vespera Analytics Platform: how data is generated,
extracted, loaded, and (in later phases) transformed into the
enterprise dimensional model that powers Looker Studio dashboards.

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
dbt Staging Models (stg_)
│
▼
dbt Mart Models (dim_, fact_*)
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
`python/generators/` — 12 generator modules, orchestrated by
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

### Output Volume (current run)

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

### Reproducibility
Fixed random seed (`RANDOM_SEED = 42`, `config.py`), applied
independently within each generator function. Re-running
`generate_data.py` produces byte-identical output.

### Known Limitations
See `00_data_generation_assumptions.md` for the full list of
deliberate simplifications made in this layer.

---

## 4. Stage 2 — Load to BigQuery (Planned)

### Target
Dataset: `vespera_dw_raw`
Project: [fill in GCP project ID once created]

### Load Method
[To be finalized — options under consideration:]
- `bq load` CLI, scripted per table
- Python client (`google-cloud-bigquery`), looping over
  `data/raw/*.csv`
- Manual console upload (not recommended at current row volumes)

**Decision:** [fill in once chosen]

### Schema Handling
Raw tables are loaded with auto-detected or explicitly defined
schema (TBD) matching the CSV output of each generator. No
transformation or cleaning happens at this stage — raw load only,
consistent with an ELT (not ETL) pattern. All business logic and
cleaning happens in dbt (Stage 3).

### Partitioning & Clustering
Per the Physical ERD & BigQuery Specification
(`docs/02_architecture/04_physical_erd.md`), the following
partitioning strategy is planned for high-volume tables:

| Table | Partition Column | Cluster Columns |
|---|---|---|
| `order_items` | (via joined `orders.order_date`) | `product_id`, `warehouse_id` |
| `orders` | `order_date` | `fulfillment_warehouse_id`, `sales_channel` |
| `inventory_movements` | `movement_date` | `warehouse_id`, `product_id` |
| `purchase_orders` | `order_date` | `warehouse_id`, `supplier_id` |
| `inventory_snapshot` | `snapshot_date` | `warehouse_id` |

[Confirm/refine once actual query patterns from dashboard design
are known.]

---

## 5. Stage 3 — Transform with dbt (Planned)

See `02_dbt_transformation_spec.md` (to be completed once dbt
project structure is scaffolded).

Planned layers:
- **Staging (`stg_*`):** 1:1 with raw tables, light cleaning,
  type casting, column renaming to enterprise naming standards.
- **Marts (`dim_*`, `fact_*`):** Kimball-style dimensional model
  per the Star Schema Architectural Specification
  (`docs/02_architecture/03_star_schema.md`).
- **Data quality tests:** per the Enterprise Data Quality Rules &
  Assertions in the Data Dictionary
  (`docs/02_architecture/05_data_dictionary.md`).

---

## 6. Stage 4 — Dashboards (Planned)

Looker Studio, connected to BigQuery mart tables (never raw
tables). Build order per project overview: Executive → Supply
Chain → Finance → Marketing.

---

## 7. Pipeline Status Checklist

- [x] Python generator layer (13 generators + orchestrator)
- [x] Data generation assumptions documented
- [ ] BigQuery raw dataset created and loaded
- [ ] Partitioning/clustering applied
- [ ] dbt project scaffolded
- [ ] dbt staging models
- [ ] dbt mart models (dimensions)
- [ ] dbt mart models (facts)
- [ ] dbt data quality tests
- [ ] Looker Studio dashboards