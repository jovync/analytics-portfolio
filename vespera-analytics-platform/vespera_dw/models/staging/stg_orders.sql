with source as (

    select * from {{ source('vespera_raw', 'raw_orders') }}

),

renamed as (

    select
        order_id,
        customer_id,
        order_date,
        sales_channel,             -- Shopify | Shopee | Lazada | Retail — order-level, not warehouse-level
        payment_method,
        order_status,
        fulfillment_warehouse_id   as warehouse_id

    from source

)

select * from renamed
