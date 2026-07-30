# Vespera dbt Project

Transforms `vespera_dw_raw` (13 raw tables, loaded via `python/load_to_bigquery.py`)
into staging views and, in a later pass, the `dim_*`/`fact_*` marts defined in
`docs/02_architecture/03_star_schema.md`.

## One-time setup

```bash
# From the vespera_dw/ directory (this folder)
pip install dbt-bigquery --break-system-packages   # or inside a venv, no flag needed
dbt deps                                            # installs dbt_utils per packages.yml

# Authenticate to GCP (if you haven't already)
gcloud auth application-default login

# Copy the profile template OUTSIDE the repo — see the file for why
cp ../profiles.yml.example ~/.dbt/profiles.yml
```

Then sanity-check the connection:

```bash
dbt debug
```

## Dataset layout

| Layer | Dataset | Materialization | Managed by |
|---|---|---|---|
| Raw | `vespera_dw_raw` | Tables | `python/load_to_bigquery.py` (not dbt) |
| Staging | `vespera_dw_staging` | Views | dbt (`models/staging/`) |
| Marts | `vespera_dw` | Tables | dbt (`models/marts/`, not yet built) |

The staging → `vespera_dw_staging` split happens automatically: `dbt_project.yml`
sets `+schema: staging` on the staging folder, and dbt-bigquery appends that to
your profile's target dataset (`vespera_dw`) by default, giving `vespera_dw_staging`.
No custom `generate_schema_name` macro needed for this simple a layout.

## Running it

```bash
dbt run --select staging      # build all 13 staging views
dbt test --select staging     # run the tests in _vespera__staging_models.yml
```

## Known follow-ups before this is "done"

A few staging models were written without independently confirming every
column against the live table (project knowledge search surfaced most
generator source, but not all of it with certainty). After your first
`dbt run`, check these against BigQuery and tighten the models if anything's off:

- **`stg_order_items`** — `tax_amount` and `commission_amount` are referenced
  per the project handoff notes but weren't visible in the generator snapshot
  I could inspect directly.
- **`stg_returns`** — same caveat for `refunded_amount` / `restocking_fee_amount`.
- **`stg_shipments`**, **`stg_inventory_movements`**, **`stg_marketing_spend`** —
  written as `SELECT *` pass-throughs rather than explicit column lists,
  since I had only partial visibility into their exact schemas. Worth
  tightening to explicit, cast, renamed columns (matching the style of
  the other 10 staging models) once you can see the real columns via:

  ```sql
  SELECT column_name, data_type
  FROM vespera_dw_raw.INFORMATION_SCHEMA.COLUMNS
  WHERE table_name = 'raw_shipments'  -- etc.
  ```

- **`stg_purchase_orders`** — the `po_status` `accepted_values` test lists a
  best-guess set of statuses (`Pending`, `Received`, `Cancelled`, `Partially
  Received`) at `severity: warn` rather than `error`, since it wasn't
  cross-checked against `config.py`'s actual `PO_STATUS` weights. Tighten
  once confirmed.

## Next steps (not in this pass)

- `models/marts/` — `dim_product`, `dim_customer`, `dim_warehouse`, `dim_date`,
  `dim_supplier`, `fact_sales`, `fact_purchase_orders`, `fact_returns`, and
  `fact_inventory_daily` (the last one needs deriving from snapshot +
  movements via a window function — it isn't a direct 1:1 staging model).
- `docs/03_engineering/02_dbt_transformation_spec.md` — currently a stub;
  fill in once the mart layer design is settled.
- `docs/03_engineering/03_data_quality_framework.md` — same.
