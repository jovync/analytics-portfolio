-- Bridge table: which (warehouse, product) pairs are actually stocked.
-- Source of truth shared by inventory_snapshot, purchase_orders, and
-- order_items generators — anything NOT in this table should never
-- appear as warehouse/product activity in those facts either.

with source as (

    select * from {{ source('vespera_raw', 'raw_warehouse_product_assignment') }}

),

renamed as (

    select
        warehouse_id,
        product_id

    from source

)

select * from renamed
