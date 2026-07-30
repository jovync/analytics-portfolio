-- SCD Type 1 (current-state only). True SCD Type 2 history isn't
-- possible yet since the raw data is a single point-in-time
-- generation, not a change stream — revisit with dbt snapshots if/when
-- the pipeline starts running on a recurring schedule against a
-- source that actually changes.

with stg as (

    select * from {{ ref('stg_products') }}

),

renamed as (

    select
        farm_fingerprint(product_id)   as product_key,
        product_id,
        sku_code,
        product_name,
        category                        as category_name,
        brand                           as brand_name,
        base_cost_sgd,
        msrp_sgd,
        launch_date,
        lifecycle_status,
        discontinued_date,
        popularity_weight,
        return_rate,
        is_currently_sellable

    from stg

),

unknown_member as (

    select
        -1                     as product_key,
        'UNKNOWN'               as product_id,
        'UNKNOWN'               as sku_code,
        'Unknown Product'       as product_name,
        'Unknown'               as category_name,
        'Unknown'               as brand_name,
        cast(null as numeric)   as base_cost_sgd,
        cast(null as numeric)   as msrp_sgd,
        cast(null as date)      as launch_date,
        'Unknown'               as lifecycle_status,
        cast(null as date)      as discontinued_date,
        cast(null as float64)   as popularity_weight,
        cast(null as float64)   as return_rate,
        false                   as is_currently_sellable

),

final as (

    select * from renamed
    union all
    select * from unknown_member

)

select * from final
