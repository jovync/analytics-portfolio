-- Grain: one row per (warehouse, product, day).
--
-- quantity_on_hand is a DERIVED balance: calibration offset (see
-- int_inventory_balance_offset) + the ledger's running cumulative
-- change as of that day, forward-filled across days with no movement
-- events (inventory doesn't reset between sales — LAST_VALUE ... IGNORE
-- NULLS carries the last known balance forward).
--
-- quantity_reserved / quantity_available / safety_stock / reorder_point
-- from raw_inventory_snapshot are deliberately NOT included here —
-- they only exist as a single point-in-time reading, not a real daily
-- series, and fabricating a daily trend for them would be misleading.
-- If those become genuinely needed at daily grain, that requires new
-- raw source data, not a derivation from what exists today.
--
-- Small negative quantity_on_hand values on a handful of
-- (warehouse, product) pairs are expected — see the ~7 residual
-- negative-balance combos already documented as accepted stockout
-- noise in 00_data_generation_assumptions.md.

with spine as (

    select * from {{ ref('int_inventory_daily_spine') }}

),

running_totals as (

    select * from {{ ref('int_inventory_movement_running_totals') }}

),

offsets as (

    select * from {{ ref('int_inventory_balance_offset') }}

),

dim_date as (

    select * from {{ ref('dim_date') }}

),

dim_product as (

    select * from {{ ref('dim_product') }}

),

dim_warehouse as (

    select * from {{ ref('dim_warehouse') }}

),

-- End-of-day state for days that actually had at least one movement:
-- the cumulative total as of the LAST event that day (not the max
-- value — cumulative can dip and recover, so "last" and "max" aren't
-- the same thing), plus a same-day breakdown by movement type.
daily_movement_summary as (

    select
        warehouse_id,
        product_id,
        date(movement_date) as movement_day,

        array_agg(
            cumulative_qty_change
            order by movement_date desc, movement_id desc
            limit 1
        )[offset(0)] as day_end_cumulative,

        sum(case when movement_type = 'CUSTOMER_SALE' then -quantity else 0 end)
            as units_sold_qty,
        sum(case when movement_type = 'CUSTOMER_RETURN' then quantity else 0 end)
            as units_returned_qty,
        sum(case when movement_type = 'INBOUND_PURCHASE' then quantity else 0 end)
            as units_received_qty

    from running_totals
    group by 1, 2, 3

),

spine_with_daily_events as (

    select
        s.warehouse_id,
        s.product_id,
        s.balance_date,
        m.day_end_cumulative,
        coalesce(m.units_sold_qty, 0)     as units_sold_qty,
        coalesce(m.units_returned_qty, 0) as units_returned_qty,
        coalesce(m.units_received_qty, 0) as units_received_qty

    from spine s
    left join daily_movement_summary m
        on s.warehouse_id = m.warehouse_id
        and s.product_id = m.product_id
        and s.balance_date = m.movement_day

),

forward_filled as (

    select
        *,
        last_value(day_end_cumulative ignore nulls) over (
            partition by warehouse_id, product_id
            order by balance_date
            rows between unbounded preceding and current row
        ) as cumulative_qty_change_as_of_day

    from spine_with_daily_events

),

with_offset as (

    select
        f.warehouse_id,
        f.product_id,
        f.balance_date,
        f.units_sold_qty,
        f.units_returned_qty,
        f.units_received_qty,
        coalesce(o.opening_balance_offset, 0) as opening_balance_offset,
        coalesce(f.cumulative_qty_change_as_of_day, 0) as cumulative_qty_change_as_of_day

    from forward_filled f
    left join offsets o
        on f.warehouse_id = o.warehouse_id
        and f.product_id = o.product_id

),

final as (

    select
        farm_fingerprint(
            concat(w.warehouse_id, '|', w.product_id, '|', cast(w.balance_date as string))
        ) as inventory_fact_key,

        coalesce(dd.date_key, -1)     as snapshot_date_key,
        coalesce(dp.product_key, -1)  as product_key,
        coalesce(dw.warehouse_key, -1) as warehouse_key,

        w.balance_date,

        w.opening_balance_offset + w.cumulative_qty_change_as_of_day
            as quantity_on_hand,

        w.units_sold_qty,
        w.units_returned_qty,
        w.units_received_qty

    from with_offset w
    left join dim_date dd
        on w.balance_date = dd.full_date
    left join dim_product dp
        on w.product_id = dp.product_id
    left join dim_warehouse dw
        on w.warehouse_id = dw.warehouse_id

)

select * from final
