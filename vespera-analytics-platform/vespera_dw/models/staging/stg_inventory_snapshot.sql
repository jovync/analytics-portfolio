with source as (

    select * from {{ source('vespera_raw', 'raw_inventory_snapshot') }}

),

renamed as (

    select
        inventory_snapshot_id,
        snapshot_date,
        warehouse_id,
        product_id,
        quantity_on_hand,
        quantity_reserved,
        quantity_available,
        safety_stock,
        reorder_point,
        inventory_value

    from source

)

select * from renamed
