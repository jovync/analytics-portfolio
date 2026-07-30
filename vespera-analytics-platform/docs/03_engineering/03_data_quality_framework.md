# Data Quality Framework

**Project:** Vespera Lifestyle Analytics Platform
**Status:** dbt test coverage implemented across all layers (91 tests, all passing)
**Last Updated:** 2026-07-30

---

## 1. Purpose

This document describes how data quality is actually verified in
this project — both the automated dbt tests that run on every build,
and the manual verification practice that supplements them. It's
written from what's actually implemented, not from an aspirational
target; §6 explains a real gap those automated tests can't cover and
how it was caught anyway.

---

## 2. Testing Strategy

Two layers of verification, doing different jobs:

1. **Automated dbt tests** — structural integrity, run on every
   `dbt test` invocation. Fast, comprehensive, catches anything a
   schema/relationship/uniqueness violation would cause. Implemented
   using dbt's built-in generic tests only (`unique`, `not_null`,
   `accepted_values`, `relationships`) — `dbt-expectations` is not
   currently a dependency; `dbt_utils` is installed via `packages.yml`
   but no `dbt_utils`-specific tests are in use yet (e.g.
   `dbt_utils.accepted_range` for measure sanity bounds — a
   reasonable next addition, see §6).

2. **Manual spot-checks against ground truth** — targeted, run when a
   model involves derived/computed logic rather than a straight
   source mirror. Slower, not automated, but catches a category of
   problem the tests above structurally cannot: values that are each
   individually valid but collectively implausible. See §6 for why
   this matters in practice, not just in theory.

---

## 3. Automated Test Inventory

91 tests total across 25 models, all passing as of last full
`dbt run` + `dbt test`.

| Layer | Tests | Coverage |
|---|---:|---|
| Sources (`raw_*`) | ~24 | `not_null`/`unique` on each table's primary natural key |
| Staging (`stg_*`) | 48 | Uniqueness/not-null on natural keys, `accepted_values` on `warehouse_type`/`sales_channel`/`po_status`, `relationships` on the warehouse/product assignment bridge and order-items→orders |
| Intermediate (`int_*`) | 9 | Uniqueness/not-null on the running-totals model's grain, not-null on the offset model's join keys |
| Marts (`dim_*`/`fact_*`) | ~34 | Uniqueness/not-null on every surrogate key, `relationships` from every fact's foreign key to its dimension's surrogate key |

### Test Categories, With Real Examples From This Project

**Uniqueness** — every surrogate and natural key across every
staging model, dimension, and fact. Example: `unique` on
`fact_inventory_daily.inventory_fact_key`, guarding against the
daily-spine join accidentally fanning out and duplicating a
(warehouse, product, day) row.

**Not-null** — same key set, ensures no row silently lost its
identity through a join.

**Accepted values** — used where a column has a small, confirmable
set of real values. `stg_purchase_orders.po_status` is the
instructive example here: it was *initially* configured with a
guessed 4-value list at `severity: warn` (`Pending`, `Received`,
`Cancelled`, `Partially Received`), which correctly fired a warning
on first real run — the actual data only ever contains `Received`
and `In Transit`. Fixed to the confirmed 2-value list at full
`severity: error` once verified against `INFORMATION_SCHEMA` output.
This is the pattern to use whenever a column's real value set isn't
already confirmed: guess conservatively, warn rather than block, then
tighten once verified — never assert a guessed enum at blocking
severity.

**Relationships** — every fact-to-dimension foreign key. These tests
only pass cleanly because every dimension carries a `-1`
unknown-member row (see `02_dbt_transformation_spec.md` §6.1) — a
fact row whose FK doesn't resolve gets coalesced to `-1` rather than
silently dropped or left null, so the relationship test has something
valid to resolve to either way.

---

## 4. Referential Integrity Pattern: Unknown Member Handling

Every dimension in this project reserves surrogate key `-1` for an
"Unknown" member row. Every fact-building model uses
`COALESCE(dimension_key, -1)` rather than a plain join, so a fact row
with a foreign key that doesn't resolve to a real dimension member
still gets a row — attributed to "Unknown" — instead of silently
disappearing from an inner join or carrying a `NULL` that breaks
`relationships` tests and downstream aggregations alike. This is the
mechanism referenced generically in `05_data_dictionary.md`'s
Referential Integrity rule 5 ("Unknown Member Handling") — this
section documents how it's actually implemented, not just asserted.

---

## 5. Business Rule Assertions — Actual vs. Aspirational

`05_data_dictionary.md` §6 lists 11 business-rule assertions as the
target data quality rule set. Honest status of each against what's
actually implemented today:

| # | Rule | Status |
|---|---|---|
| 1 | Surrogate key uniqueness | ✅ Implemented (§3) |
| 2 | Natural key uniqueness | ✅ Implemented (§3) |
| 3 | Single active SCD record per entity | N/A — no SCD Type 2 dimensions exist yet (see `02_dbt_transformation_spec.md` §6.1) |
| 4 | Fact-to-dimension relationships resolve | ✅ Implemented (§3) |
| 5 | Unknown member handling | ✅ Implemented (§4) |
| 6 | Non-negative financial values | ❌ Not implemented as a dbt test |
| 7 | Discount ≤ gross revenue | ❌ Not implemented as a dbt test |
| 8 | Net revenue = gross − discount | ❌ Not implemented as a dbt test |
| 9 | Inventory ≥ 0 unless flagged adjustment | ❌ Not implemented — and notably, `fact_inventory_daily` **does** contain a small number of genuine negative balances (documented, accepted stockout noise — see `00_data_generation_assumptions.md`), so this rule needs a real exception clause before it could be safely turned on, not just a blanket assertion |
| 10 | PO received ≤ ordered | ❌ Not implemented as a dbt test |
| 11 | No future-dated timestamps | ❌ Not implemented as a dbt test — also not very meaningful for a static historical simulation with a fixed date range, versus a live incrementally-loading pipeline |

Rules 6, 7, 8, and 10 are all straightforward to add as
`dbt_utils.expression_is_true` tests on the relevant fact models and
are the natural next increment of coverage. Not added yet simply
because nothing so far has surfaced a concrete reason to need them —
worth doing before this pipeline is treated as production-grade
rather than portfolio-grade.

---

## 6. Case Study: What Automated Tests Didn't Catch

This is the most important section in this document, because it's
about a real gap, not a hypothetical one.

**What happened:** Every single dbt test passed — uniqueness,
not-null, every relationship — throughout the entire period that
`raw_purchase_orders` had a real, systemic data quality problem:
Distribution Center purchase order quantities were completely
decoupled from actual product demand, with the same handful of round
numbers (1,600, 4,500, etc.) repeating across dozens of unrelated
products. It was caught by manually inspecting one
(warehouse, product) pair's day-by-day balance in
`fact_inventory_daily` and noticing a purchase receipt of 4,500 units
for a product selling ~4-9 units/day — obviously wrong to a human
glance, invisible to every test that was actually running. Full
root-cause and fix detailed in `01_etl_design.md` §7.

**Why the tests couldn't catch it:** `quantity_ordered = 4500` is a
perfectly valid `INT64`, it's `NOT NULL`, it doesn't violate any
uniqueness constraint, and it resolves to a real product and
warehouse via every `relationships` test. Structural correctness and
business plausibility are different properties, and this project's
test suite — like most dbt test suites relying only on generic tests
— only checks the former.

**What this changes going forward:** two concrete additions worth
making before more marts get built on top of this data:

1. **`dbt_utils.accepted_range` (or `expression_is_true`) tests on
   key measures**, e.g. `fact_purchase_orders.quantity_ordered`
   bounded against some multiple of the product's historical average
   order size, or `fact_inventory_daily.quantity_on_hand` bounded
   against a sane multiple of `safety_stock`. This wouldn't have
   caught the exact 4,500-unit issue automatically without tuning
   (that number wasn't statistically an outlier *within its own demand
   tier*, since every product in that tier had the same problem —
   the anomaly was only visible relative to actual sell-through,
   which lives in a different table). Still worth adding as a
   baseline sanity net for genuinely wild values.
2. **Keep the manual spot-check habit** described in
   `02_dbt_transformation_spec.md` §7 for any model built on derived
   or computed business logic, not just ones with failing tests.
   Automated tests and human judgment are catching different classes
   of problem here, and this project has direct evidence both are
   necessary.

---

## 7. Not Currently Implemented

Stated plainly rather than left implicit:

- **No CI/CD automated test runs.** `dbt test` is invoked manually.
  No GitHub Actions or equivalent runs it on push/PR.
- **No freshness tests.** Not meaningful yet — this is a static,
  point-in-time simulation with a fixed date range, not an
  incrementally-loading live pipeline. Freshness tests become
  relevant if/when the generation pipeline runs on a real schedule.
- **No `dbt-expectations` statistical tests** (distribution checks,
  outlier detection, etc.) — `dbt_utils` is installed but unused
  beyond being available; `dbt-expectations` isn't a dependency at
  all yet.