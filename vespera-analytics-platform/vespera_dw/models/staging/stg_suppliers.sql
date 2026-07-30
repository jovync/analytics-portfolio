with source as (

    select * from {{ source('vespera_raw', 'raw_suppliers') }}

),

renamed as (

    select
        supplier_id,
        trim(supplier_name)        as supplier_name,
        supplier_tier,
        category_specialty,
        country                    as supplier_country,
        currency                   as supplier_currency,
        payment_terms,
        lead_time_days,
        quality_rating,
        preferred_supplier,
        created_at                 as supplier_created_at

    from source

)

select * from renamed
