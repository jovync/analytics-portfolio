with source as (

    select * from {{ source('vespera_raw', 'raw_customers') }}

),

renamed as (

    select
        customer_id,
        trim(first_name)           as first_name,
        trim(last_name)            as last_name,
        lower(trim(email))         as email_address,
        phone                      as phone_number,
        country                    as customer_country,
        gender,
        birth_date,
        customer_since,
        loyalty_tier,
        acquisition_channel,
        customer_status

    from source

)

select * from renamed
