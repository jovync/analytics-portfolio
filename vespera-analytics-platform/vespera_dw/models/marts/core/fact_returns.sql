-- Grain: one row per returned order line item.
--
-- refunded_amount and restocking_fee_amount are DERIVED here, not
-- sourced directly — raw_returns doesn't have them (confirmed against
-- BigQuery INFORMATION_SCHEMA on 2026-07-30; see stg_returns.sql).
-- Business logic follows 00_data_generation_assumptions.md's original
-- intent: refund prorated by returned quantity against the order
-- item's actual net unit price, and a 10% restocking fee applied only
-- when return_reason is "Customer Remorse". This resolves the
-- fact_returns doc/data divergence flagged when the staging layer was
-- built — 03_star_schema.md / 05_data_dictionary.md should be updated
-- to note these are derived mart-layer measures, not raw source
-- columns, the next time those docs get a reconciliation pass.

with returns as (

    select * from {{ ref('stg_returns') }}

),

order_items as (

    select * from {{ ref('stg_order_items') }}

),

orders as (

    select * from {{ ref('stg_orders') }}

),

dim_customer as (

    select * from {{ ref('dim_customer') }}

),

dim_product as (

    select * from {{ ref('dim_product') }}

),

dim_warehouse as (

    select * from {{ ref('dim_warehouse') }}

),

dim_date as (

    select * from {{ ref('dim_date') }}

),

joined as (

    select
        r.return_id,
        r.order_id,
        r.order_item_id,
        r.product_id,
        r.warehouse_id,
        r.return_date,
        r.returned_quantity,
        r.return_reason,
        r.disposition_code,

        o.customer_id,
        o.order_date                                       as original_order_date,

        -- Per-unit net price from the original line item, used to
        -- prorate the refund by returned quantity.
        safe_divide(oi.net_sales, oi.quantity)              as unit_net_price,

        r.returned_quantity * safe_divide(oi.net_sales, oi.quantity)
                                                             as refunded_amount

    from returns r
    inner join orders o
        on r.order_id = o.order_id
    left join order_items oi
        on r.order_item_id = oi.order_item_id

),

with_fee as (

    select
        *,
        case
            when return_reason = 'Customer Remorse'
                then round(refunded_amount * 0.10, 2)
            else 0.0
        end as restocking_fee_amount

    from joined

),

final as (

    select
        farm_fingerprint(w.return_id)          as return_fact_key,
        coalesce(dd_return.date_key, -1)        as return_date_key,
        coalesce(dd_original.date_key, -1)      as original_order_date_key,
        coalesce(dc.customer_key, -1)           as customer_key,
        coalesce(dp.product_key, -1)            as product_key,
        coalesce(dw.warehouse_key, -1)          as warehouse_key,

        w.return_id                              as return_authorization_number,
        w.disposition_code,
        w.return_reason                          as return_reason_code,

        w.returned_quantity,
        round(w.refunded_amount, 2)              as refunded_amount,
        w.restocking_fee_amount

    from with_fee w
    left join dim_date dd_return
        on date(w.return_date) = dd_return.full_date
    left join dim_date dd_original
        on date(w.original_order_date) = dd_original.full_date
    left join dim_customer dc
        on w.customer_id = dc.customer_id
    left join dim_product dp
        on w.product_id = dp.product_id
    left join dim_warehouse dw
        on w.warehouse_id = dw.warehouse_id

)

select * from final
