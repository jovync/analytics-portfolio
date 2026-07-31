-- Executive Dashboard, Page 1 — Overview Scorecard
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- One row per calendar day, 2024-01-01 through 2025-12-31 (matches
-- the simulation window used everywhere else in this project).
--
-- IMPORTANT — read before building calculated fields in Looker Studio:
-- All ratio metrics (Gross Margin %, AOV, Return Rate) are returned
-- here as their raw numerator/denominator components, NOT as
-- pre-divided percentages. Build the division as a Looker Studio
-- calculated field using SUM() on each component — this is what
-- makes the ratio aggregate correctly no matter what date range or
-- grouping you apply. If you divide in this SQL instead, Looker
-- Studio will average the daily ratios when you widen the date
-- range, which is NOT the same number as the true period ratio.
--
-- active_skus / stockout_skus are a DIFFERENT case: these are daily
-- SNAPSHOT counts (how many SKU x warehouse combos exist / are
-- stocked out on that specific day), not transactions. Summing them
-- across a date range is meaningless (double-counts the same SKU on
-- every day it's stocked out). In Looker Studio, right-click each of
-- these two fields > change default aggregation to AVERAGE, not SUM
-- — this gives you "average daily stockout rate over the period,"
-- which is the correct read for a trend scorecard. A true "stockout
-- rate as of right now" would need a separate query filtered to the
-- single latest date, which we can build later if you want that
-- exact framing instead.

with date_spine as (

    select
        full_date as report_date,
        date_key

    from `vespera-analytics-platform.vespera_dw.dim_date`
    where full_date between '2024-01-01' and '2025-12-31'

),

daily_sales as (

    select
        order_date_key,
        sum(net_revenue_amount) as net_revenue_amount,
        sum(cogs_amount)        as cogs_amount,
        sum(quantity_ordered)   as sold_units,

        -- Completed orders = distinct orders, excluding cancelled.
        -- fulfillment_status values assumed to include 'Cancelled'
        -- per the ORDER_STATUS config — worth a quick eyeball once
        -- this runs to confirm the exact string matches.
        count(distinct case
            when fulfillment_status != 'Cancelled' then order_number
        end) as completed_orders

    from `vespera-analytics-platform.vespera_dw.fact_sales`
    group by order_date_key

),

daily_returns as (

    select
        return_date_key,
        sum(returned_quantity) as returned_units

    from `vespera-analytics-platform.vespera_dw.fact_returns`
    group by return_date_key

),

daily_inventory as (

    select
        snapshot_date_key,

        count(distinct concat(cast(product_key as string), '-', cast(warehouse_key as string)))
            as active_skus,

        count(distinct case
            when quantity_on_hand <= 0
            then concat(cast(product_key as string), '-', cast(warehouse_key as string))
        end) as stockout_skus

    from `vespera-analytics-platform.vespera_dw.fact_inventory_daily`
    group by snapshot_date_key

)

select

    ds.report_date,

    coalesce(s.net_revenue_amount, 0) as net_revenue_amount,
    coalesce(s.cogs_amount, 0)        as cogs_amount,
    coalesce(s.sold_units, 0)         as sold_units,
    coalesce(s.completed_orders, 0)   as completed_orders,

    coalesce(r.returned_units, 0)     as returned_units,

    coalesce(i.active_skus, 0)        as active_skus,
    coalesce(i.stockout_skus, 0)      as stockout_skus

from date_spine ds
left join daily_sales s
    on ds.date_key = s.order_date_key
left join daily_returns r
    on ds.date_key = r.return_date_key
left join daily_inventory i
    on ds.date_key = i.snapshot_date_key

order by ds.report_date
