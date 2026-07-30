with source as (

    select * from {{ source('vespera_raw', 'raw_purchase_orders') }}

),

renamed as (

    select
        purchase_order_id,
        supplier_id,
        product_id,
        warehouse_id,
        order_date,
        expected_receipt_date,
        actual_receipt_date,
        quantity_ordered,
        quantity_received,
        unit_cost_sgd,
        total_cost_sgd,
        po_status,
        demand_tier,

        date_diff(expected_receipt_date, order_date, day) as expected_lead_time_days

    from source

)

select * from renamed
