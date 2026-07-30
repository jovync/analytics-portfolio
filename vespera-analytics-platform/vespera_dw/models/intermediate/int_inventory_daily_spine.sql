-- One row per (warehouse, product, day) — but only for days where
-- that product is both (a) actually assigned/stocked at that
-- warehouse (per stg_warehouse_product_assignment, the same shared
-- source of truth the raw generators used) and (b) within its active
-- product lifecycle window, intersected with the simulation period
-- (movements only exist 2024-01-01 to 2025-12-31 — a product launched
-- in 2022 doesn't get ledger-backed daily rows for 2022-2023).
--
-- Expect on the order of a few million rows (4,756 assignment pairs
-- × up to ~730 days each) — normal for a daily grain fact at this
-- scale, not a bug if the row count looks large.

with assignment as (

    select * from {{ ref('stg_warehouse_product_assignment') }}

),

dim_product as (

    select * from {{ ref('dim_product') }}
    where product_id != 'UNKNOWN'

),

dim_date as (

    select * from {{ ref('dim_date') }}

),

bounded_products as (

    select
        product_id,
        greatest(launch_date, date('2024-01-01'))
            as window_start,
        least(coalesce(discontinued_date, date('2025-12-31')), date('2025-12-31'))
            as window_end

    from dim_product

),

spine as (

    select
        a.warehouse_id,
        a.product_id,
        d.full_date as balance_date

    from assignment a
    inner join bounded_products bp
        on a.product_id = bp.product_id
    inner join dim_date d
        on d.full_date between bp.window_start and bp.window_end

)

select * from spine
