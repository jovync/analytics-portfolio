-- One row per (warehouse, product) in raw_inventory_snapshot (~4,016
-- rows). Calculates the calibration offset that anchors the running
-- ledger total to the one real balance we actually have.
--
-- The ledger only tells us how much inventory CHANGED at each event —
-- it has no concept of a starting balance. So:
--
--   opening_balance_offset = snapshot.quantity_on_hand
--                             - (cumulative ledger change as of snapshot_date)
--
-- Add that offset to the running total on ANY date and you get a real
-- balance, because it's calibrated to a date we know is correct.

with snapshot as (

    select * from {{ ref('stg_inventory_snapshot') }}

),

running_totals as (

    select * from {{ ref('int_inventory_movement_running_totals') }}

),

-- Last movement on or before the snapshot date, per (warehouse, product).
-- LEFT JOIN + QUALIFY handles both cases: pairs with prior movements
-- (picks the latest one) and pairs with none yet as of the snapshot
-- date (single NULL-matched row, cumulative treated as 0 below).
anchor_movement as (

    select
        s.warehouse_id,
        s.product_id,
        s.snapshot_date,
        s.quantity_on_hand as snapshot_quantity_on_hand,
        r.cumulative_qty_change as cumulative_at_snapshot

    from snapshot s
    left join running_totals r
        on s.warehouse_id = r.warehouse_id
        and s.product_id = r.product_id
        and date(r.movement_date) <= s.snapshot_date

    qualify row_number() over (
        partition by s.warehouse_id, s.product_id
        order by r.movement_date desc, r.movement_id desc
    ) = 1

),

offset_calc as (

    select
        warehouse_id,
        product_id,
        snapshot_date,
        snapshot_quantity_on_hand,
        coalesce(cumulative_at_snapshot, 0) as cumulative_at_snapshot,
        snapshot_quantity_on_hand - coalesce(cumulative_at_snapshot, 0)
            as opening_balance_offset

    from anchor_movement

)

select * from offset_calc
