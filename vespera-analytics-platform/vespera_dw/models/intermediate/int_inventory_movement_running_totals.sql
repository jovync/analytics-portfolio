-- One row per movement event (mirrors raw_inventory_movements' grain,
-- 192,199 rows), with a running cumulative signed-quantity total per
-- (warehouse, product) added on top. This is a RUNNING TOTAL OF
-- CHANGES, not yet a real balance — see int_inventory_balance_offset
-- for the calibration step that turns it into one.
--
-- Materialized as a table (not the usual staging-style view) since
-- the window function here is the expensive part of the whole
-- fact_inventory_daily chain and shouldn't be recomputed on every
-- downstream reference.

{{ config(materialized='table') }}

with movements as (

    select * from {{ ref('stg_inventory_movements') }}

),

running_totals as (

    select
        movement_id,
        movement_date,
        movement_type,
        warehouse_id,
        product_id,
        quantity,

        sum(quantity) over (
            partition by warehouse_id, product_id
            order by movement_date, movement_id
            rows between unbounded preceding and current row
        ) as cumulative_qty_change

    from movements

)

select * from running_totals
