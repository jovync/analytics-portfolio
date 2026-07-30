with stg as (

    select * from {{ ref('stg_suppliers') }}

),

renamed as (

    select
        farm_fingerprint(supplier_id)  as supplier_key,
        supplier_id,
        supplier_name,
        supplier_tier,
        category_specialty,
        supplier_country,
        supplier_currency,
        payment_terms,
        lead_time_days,
        quality_rating,
        preferred_supplier

    from stg

),

unknown_member as (

    select
        -1                      as supplier_key,
        'UNKNOWN'                as supplier_id,
        'Unknown Supplier'       as supplier_name,
        'Unknown'                as supplier_tier,
        'Unknown'                as category_specialty,
        'Unknown'                as supplier_country,
        'Unknown'                as supplier_currency,
        cast(null as string)     as payment_terms,
        cast(null as int64)      as lead_time_days,
        cast(null as float64)    as quality_rating,
        cast(null as bool)       as preferred_supplier

),

final as (

    select * from renamed
    union all
    select * from unknown_member

)

select * from final
