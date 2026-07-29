# Data Generation Assumptions & Known Limitations

**Project:** Vespera Lifestyle Analytics Platform
**Layer:** Synthetic Data Generation (python/)
**Status:** Complete
**Last Updated:** [fill in date]

---

## 1. Purpose

This document records the deliberate simplifications, design
decisions, and known limitations made while building the synthetic
enterprise data generation layer (`python/generators/`). It exists
so that downstream work — BigQuery loading, dbt transformations,
and dashboard design — is built with full awareness of what the raw
data does and does not represent.

Some decisions here diverge from the original Phase 1/2 planning
documentation (Business Capability Model, Enterprise Data Model,
Star Schema Spec, Data Dictionary). Where that happens, it's called
out explicitly, since those documents were written before
implementation surfaced these tradeoffs.

---

## 2. Currency

All monetary fields across the dataset are generated in a single
reporting currency: **SGD (Singapore Dollar)**.

- `products.py` generates `base_cost_sgd` and `msrp_sgd`.
- `purchase_orders.py` generates `unit_cost_sgd` / `total_cost_sgd`.
- `suppliers.py` assigns each supplier a local invoicing `currency`
  (CNY, THB, MYR, SGD, IDR, USD) reflecting their home market, but
  **this field is decorative and is not used in any FX conversion.**
  All supplier costs still flow into `products.py` already
  denominated in SGD.

**Divergence from planning docs:** the Enterprise KPI & Metric
Catalog in the data dictionary specifies `_usd` suffixed field names
(`gross_revenue_usd`, `net_revenue_usd`, `cogs_usd`). The
implemented data model uses `_sgd` throughout instead, since Vespera
is Singapore-headquartered and SGD is the more defensible reporting
currency for this business. The data dictionary should be updated
to reflect `_sgd` naming, or dbt staging models should alias
accordingly.

---

## 3. Warehouse & Store Modeling

Retail Stores, Distribution Centers, and the Returns Center are
modeled as a **single `warehouses` table**, distinguished by a
`warehouse_type` field, rather than as separate Store and Warehouse
dimensions.

**Divergence from planning docs:** the Data Dictionary's
`fact_returns` and other fact specs reference `store_sk` and
`warehouse_sk` as two distinct foreign keys. In the implemented
model, both resolve to the same `dim_warehouse` (or `dim_location`)
table filtered by `warehouse_type`. If strict adherence to the
original two-dimension design is required downstream, this can be
addressed at the dbt layer by splitting `dim_warehouse` into two
views rather than reworking the generators.

Each warehouse has a `serves_countries` list controlling which
customer countries it's eligible to fulfill orders for:
- Retail Stores only fulfill **online or in-person orders placed
  within their own country** (channel = "Retail" is restricted to
  same-country stores only).
- Distribution Centers serve a small regional cluster of countries
  that lack their own physical store (e.g. the Malaysia DC also
  serves Thailand and Vietnam online orders).

---

## 4. Warehouse-Product Assignment

Which products a given warehouse actually stocks is determined by a
single shared assignment table (`generators/assignment.py`,
persisted as `warehouse_product_assignment.csv`), computed once and
reused across `inventory_snapshot.py`, `purchase_orders.py`, and
`order_items.py`.

- Distribution Centers carry 100% of eligible products.
- Retail Stores carry a random 35% subset.
- Products in the top two demand-tier quartiles (High / Very High,
  based on `popularity_weight` percentile rank) are **force-assigned
  to every warehouse**, reflecting that a real retailer's
  best-sellers are stocked everywhere.

This shared-assignment design was introduced specifically to fix an
early bug where opening inventory, purchase order replenishment,
and actual sales were each computed independently and could
disagree about what a given warehouse carried — resulting in
warehouses selling products they were never stocked or replenished
with. See Section 8 for the residual effect of this fix.

---

## 5. Purchase Order Fulfillment Model

Purchase orders flow **directly from supplier to every assigned
warehouse**, including retail stores, rather than modeling an
internal DC → store transfer network.

**Simplification:** in a real enterprise, retail stores are
typically replenished via internal stock transfers from a
Distribution Center, not direct supplier shipment. `config.py`'s
`INVENTORY_MOVEMENT_TYPES` reserves 12% of movement volume for
`"Stock Transfer"`, but no generator currently produces this
movement type — it's a documented gap, and a candidate for a future
`stock_transfers.py` generator if DC → store logistics realism
becomes a project priority.

Order quantity and reorder cycle length both scale by each
product's demand tier (`DEMAND_TIER_QUANTITY_MULTIPLIER`,
`DEMAND_TIER_CYCLE_DIVISOR` in `purchase_orders.py`), so
higher-demand SKUs are replenished in larger batches, more
frequently.

---

## 6. Product Lifecycle

- **85%** of products are backdated as already existing before the
  simulation start date (`launch_date` 30–900 days before
  `SIMULATION_START_DATE`), reflecting a retailer with an
  established catalog on day one.
- The remaining **15%** are genuine new launches, with
  `launch_date` falling within the simulation window.
- Products launching within 60 days of `SIMULATION_END_DATE` are
  always tagged `"New Launch"`. Otherwise, lifecycle status is
  `"Active"` (85%) or `"Discontinued"` (15%), with a computed
  `discontinued_date` for the latter.
- `order_items.py` only offers a product for sale if the order date
  falls between its `launch_date` and `discontinued_date` (or
  indefinitely, if never discontinued).

---

## 7. Tax, Commission, Refunds & Restocking Fees

- **Tax:** a single flat rate per country (`TAX_RATES_BY_COUNTRY`),
  applied based on the **fulfilling warehouse's country** (point-
  of-sale jurisdiction), not the customer's billing country. No
  category-level tax exemptions are modeled.
- **Marketplace commission:** a flat rate per sales channel
  (`MARKETPLACE_COMMISSION_RATES`) — Shopee (6%) and Lazada (5%)
  charge a seller commission; Shopify and Retail do not.
- **Refunds:** `refunded_amount` is the original line's `net_sales`
  prorated by the share of quantity actually returned (a partial
  return only refunds its portion).
- **Restocking fee:** only charged when `return_reason` is
  `"Customer Remorse"` (10% of refunded amount) — not charged when
  Vespera is at fault (Damaged, Wrong Item, Sizing Issue, Not as
  Expected).

---

## 8. Inventory Ledger & Residual Stockouts

The inventory ledger (`inventory_movements.py`) is built from four
sources: opening snapshot, Customer Sale (negative), Customer
Return (positive), and Inbound Purchase (positive, from
`purchase_orders.py`).

After the warehouse-product assignment fix (Section 4), a
diagnostic check (`check_inventory_balances()` in
`generate_data.py`) reconstructs running on-hand balance per
warehouse/product and flags any that go negative.

**Current state:** 7 out of 4,756 warehouse-product combinations
end the simulation with a negative on-hand balance, all at
single-digit unit magnitude (-1 to -4 units). This is accepted as
realistic timing noise — a purchase order landing a day or two
after a local demand spike — rather than pursued to a literal zero,
since real inventory systems experience minor stockouts too.
Downstream dbt models computing daily on-hand balances may choose
to floor displayed values at zero (`GREATEST(balance, 0)`) to
prevent this from surfacing as a data quality test failure.

---

## 9. Marketing Attribution Model

`marketing_spend.py` generates daily spend at the grain of one row
per (date, campaign) for four **paid** channels: Facebook Ads,
Instagram, TikTok, Email Campaign. Organic Search and Referral
(also present in `customers.py`'s `ACQUISITION_CHANNELS`) receive
no spend rows, since they are unpaid/indirect acquisition paths by
definition.

**Attribution model:** ROAS and CAC use **first-touch attribution**
— a customer's entire lifetime `net_sales` (from `order_items`) is
attributed to their single `acquisition_channel` (assigned once, at
signup, in `customers.py`). No per-order or multi-touch marketing
attribution is modeled, since no generator links a specific order
to a specific campaign.

---

## 10. Reproducibility

All generators use `RANDOM_SEED = 42` (`config.py`). Each generator
function accepts its own `seed` parameter and reseeds internally
at the start of execution, rather than relying on a single
import-time seed and generator call order. This means the full
pipeline (`generate_data.py`) produces byte-identical output on
every re-run, and individual generators can also be run and
re-verified in isolation via their own `__main__` blocks.

---

## 11. Faker Locale Handling

Customer names/contact details are localized via
`utils.get_faker(country)`, using a fallback chain of
`[country_locale, "en_US"]`. This handles two real constraints
found during implementation: some locale providers (e.g. Thai,
Vietnamese) don't implement every method (like `phone_number()`),
and Malaysia has no valid dedicated Faker locale (`ms_MY` does not
exist in the installed Faker version) — Malaysian customers
currently fall back to `en_US`-style names.

---

## 12. Summary Table

| Area | Simplification | Future Enhancement Candidate |
|---|---|---|
| Currency | Single reporting currency (SGD) | Multi-currency FX conversion |
| Store/Warehouse | Single table, `warehouse_type` field | Split into `dim_store` / `dim_warehouse` |
| Replenishment | Direct supplier → all warehouses | DC → store internal transfers |
| Tax | Flat rate per country | Category-level exemptions/thresholds |
| Marketing attribution | First-touch, customer-level | Multi-touch, order-level attribution |
| Inventory | ~7 residual negative-balance SKUs | Zero-floor at dbt layer, or further PO tuning |