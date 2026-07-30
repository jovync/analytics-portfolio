with source as (

    select * from {{ source('vespera_raw', 'raw_products') }}

),

renamed as (

    select
        product_id,
        sku                         as sku_code,
        trim(product_name)          as product_name,
        category,
        brand,
        supplier_id,
        base_cost_sgd,
        msrp_sgd,
        launch_date,
        lifecycle_status,
        discontinued_date,
        popularity_weight,
        return_rate,
        reorder_point,
        reorder_quantity,
        lead_time_days,

        -- convenience flag: is this SKU sellable as of today
        case
            when lifecycle_status = 'Discontinued' then false
            when launch_date > current_date() then false
            else true
        end                          as is_currently_sellable

    from source

)

select * from renamed
