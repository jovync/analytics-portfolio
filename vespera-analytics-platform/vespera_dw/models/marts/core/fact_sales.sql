-- Grain: one row per order line item.
--
-- COGS is quantity × the product's CURRENT base_cost_sgd (dim_product
-- is Type 1 / current-state only), not the cost as of the order date —
-- a known simplification until dim_product tracks history.

with order_items as (

    select * from {{ ref('stg_order_items') }}

),

orders as (

    select * from {{ ref('stg_orders') }}

),

dim_product as (

    select * from {{ ref('dim_product') }}

),

dim_customer as (

    select * from {{ ref('dim_customer') }}

),

dim_warehouse as (

    select * from {{ ref('dim_warehouse') }}

),

dim_date as (

    select * from {{ ref('dim_date') }}

),

joined as (

    select
        oi.order_item_id,
        oi.order_id,
        oi.product_id,
        oi.warehouse_id,
        o.customer_id,
        date(o.order_date)             as order_date,
        o.sales_channel,
        o.payment_method,
        o.order_status                 as fulfillment_status,

        row_number() over (
            partition by oi.order_id
            order by oi.order_item_id
        )                               as line_item_number,

        oi.quantity                    as quantity_ordered,
        p.msrp_sgd                     as unit_list_price_amount,
        oi.unit_price                  as unit_selling_price_amount,
        oi.gross_sales                 as gross_revenue_amount,
        oi.discount_amount,
        oi.tax_amount,
        oi.net_sales                   as net_revenue_amount,
        oi.commission_amount,
        oi.quantity * p.base_cost_sgd  as cogs_amount

    from order_items oi
    inner join orders o
        on oi.order_id = o.order_id
    left join dim_product p
        on oi.product_id = p.product_id

),

final as (

    select
        farm_fingerprint(j.order_item_id)      as sales_fact_key,
        coalesce(dd.date_key, -1)               as order_date_key,
        coalesce(dc.customer_key, -1)           as customer_key,
        coalesce(dp.product_key, -1)            as product_key,
        coalesce(dw.warehouse_key, -1)          as warehouse_key,

        j.order_id                              as order_number,
        j.line_item_number,
        j.sales_channel                         as sales_channel_code,
        j.payment_method,
        j.fulfillment_status,

        j.quantity_ordered,
        j.unit_list_price_amount,
        j.unit_selling_price_amount,
        j.gross_revenue_amount,
        j.discount_amount,
        j.tax_amount,
        j.net_revenue_amount,
        j.commission_amount,
        j.cogs_amount

    from joined j
    left join dim_date dd
        on j.order_date = dd.full_date
    left join dim_customer dc
        on j.customer_id = dc.customer_id
    left join dim_product dp
        on j.product_id = dp.product_id
    left join dim_warehouse dw
        on j.warehouse_id = dw.warehouse_id

)

select * from final
