with source as (

    select * from {{ source('vespera_raw', 'raw_warehouses') }}

),

renamed as (

    select
        warehouse_id,
        upper(trim(warehouse_code))    as warehouse_code,
        trim(warehouse_name)           as warehouse_name,
        warehouse_type,                -- Distribution Center | Retail Store | Returns Center
        country                        as warehouse_country,
        city                           as warehouse_city,
        region                         as warehouse_region,
        serves_countries                -- array<string>; countries this facility can fulfill

    from source

)

select * from renamed
