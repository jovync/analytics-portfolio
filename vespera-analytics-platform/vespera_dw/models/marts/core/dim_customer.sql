-- SCD Type 1 (current-state only) — same rationale as dim_product.

with stg as (

    select * from {{ ref('stg_customers') }}

),

renamed as (

    select
        farm_fingerprint(customer_id)  as customer_key,
        customer_id,
        first_name,
        last_name,
        email_address,
        phone_number,
        customer_country,
        gender,
        birth_date,
        customer_since,
        loyalty_tier,
        acquisition_channel,
        customer_status

    from stg

),

unknown_member as (

    select
        -1                      as customer_key,
        'UNKNOWN'                as customer_id,
        'Unknown'                as first_name,
        'Unknown'                as last_name,
        'unknown@unknown.com'    as email_address,
        cast(null as string)     as phone_number,
        'Unknown'                as customer_country,
        cast(null as string)     as gender,
        cast(null as date)       as birth_date,
        cast(null as date)       as customer_since,
        'Unknown'                as loyalty_tier,
        'Unknown'                as acquisition_channel,
        'Unknown'                as customer_status

),

final as (

    select * from renamed
    union all
    select * from unknown_member

)

select * from final
