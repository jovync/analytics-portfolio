-- Single conformed location dimension — Distribution Centers, Retail
-- Stores, and the Returns Center. See 03_star_schema.md v1.2 for why
-- there's no separate dim_store.

with stg as (

    select * from {{ ref('stg_warehouses') }}

),

renamed as (

    select
        farm_fingerprint(warehouse_id) as warehouse_key,
        warehouse_id,
        warehouse_code,
        warehouse_name,
        warehouse_type,
        warehouse_country,
        warehouse_city,
        warehouse_region,
        serves_countries

    from stg

),

unknown_member as (

    select
        -1                      as warehouse_key,
        'UNKNOWN'                as warehouse_id,
        'UNKNOWN'                as warehouse_code,
        'Unknown Warehouse'      as warehouse_name,
        'Unknown'                as warehouse_type,
        'Unknown'                as warehouse_country,
        cast(null as string)     as warehouse_city,
        cast(null as string)     as warehouse_region,
        cast(null as string)     as serves_countries

),

final as (

    select * from renamed
    union all
    select * from unknown_member

)

select * from final
