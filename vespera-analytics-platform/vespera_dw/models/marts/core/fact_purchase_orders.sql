-- Grain: one row per purchase order (each row in raw_purchase_orders
-- is already atomic — one supplier/product/warehouse/order_date
-- combination — there's no separate PO-header-vs-line-item split in
-- this source, unlike fact_sales/order_items).
--
-- purchase_price_variance_amount compares actual unit cost paid
-- against the product's CURRENT base_cost_sgd (dim_product is Type 1),
-- not the standard cost as of the order date — same simplification
-- noted in fact_sales.

with po as (

    select * from {{ ref('stg_purchase_orders') }}

),

dim_supplier as (

    select * from {{ ref('dim_supplier') }}

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
        po.*,
        p.base_cost_sgd

    from po
    left join dim_product p
        on po.product_id = p.product_id

),

final as (

    select
        farm_fingerprint(j.purchase_order_id)   as purchase_order_fact_key,
        coalesce(dd_order.date_key, -1)          as po_date_key,
        coalesce(dd_expected.date_key, -1)       as expected_delivery_date_key,
        coalesce(ds.supplier_key, -1)            as supplier_key,
        coalesce(dp.product_key, -1)             as product_key,
        coalesce(dw.warehouse_key, -1)           as destination_warehouse_key,

        j.purchase_order_id                      as po_number,
        j.po_status                               as po_status_code,
        j.demand_tier,

        j.quantity_ordered                        as ordered_quantity,
        j.quantity_received                        as received_quantity,
        j.unit_cost_sgd                            as unit_purchase_cost_amount,
        j.total_cost_sgd                           as total_purchase_cost_amount,
        j.expected_lead_time_days                  as lead_time_days,
        (j.unit_cost_sgd - j.base_cost_sgd) * j.quantity_ordered
                                                    as purchase_price_variance_amount,

        j.actual_receipt_date

    from joined j
    left join dim_date dd_order
        on date(j.order_date) = dd_order.full_date
    left join dim_date dd_expected
        on date(j.expected_receipt_date) = dd_expected.full_date
    left join dim_supplier ds
        on j.supplier_id = ds.supplier_id
    left join dim_product dp
        on j.product_id = dp.product_id
    left join dim_warehouse dw
        on j.warehouse_id = dw.warehouse_id

)

select * from final
