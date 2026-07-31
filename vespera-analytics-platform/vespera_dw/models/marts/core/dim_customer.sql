-- SCD Type 1 (current-state only) -- same rationale as dim_product.
--
-- acquisition_campaign_key added (v1.2 KPI Framework <-> Star Schema
-- reconciliation, closing the CAC gap -- see
-- docs/06_kpi_schema_reconciliation.md). Left-joined from
-- stg_acquisition_attribution via customer_id, then coalesced to
-- dim_campaign's -1 "No Campaign (Organic/Unpaid Channel)" member
-- for customers with no paid-channel attribution -- keeps the FK
-- fully resolvable with no NULLs, matching this project's existing
-- convention (see unknown_member below).

with stg as (

    select * from {{ ref('stg_customers') }}

),

stg_acquisition_attribution as (

    select * from {{ ref('stg_acquisition_attribution') }}

),

dim_campaign as (

    select * from {{ ref('dim_campaign') }}

),

renamed as (

    select
        farm_fingerprint(stg.customer_id)  as customer_key,
        stg.customer_id,
        stg.first_name,
        stg.last_name,
        stg.email_address,
        stg.phone_number,
        stg.customer_country,
        stg.gender,
        stg.birth_date,
        stg.customer_since,
        stg.loyalty_tier,
        stg.acquisition_channel,
        stg.customer_status,

        coalesce(dc.campaign_key, -1) as acquisition_campaign_key

    from stg
    left join stg_acquisition_attribution aa
        on stg.customer_id = aa.customer_id
    left join dim_campaign dc
        on aa.acquisition_campaign_id = dc.campaign_id

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
        'Unknown'                as customer_status,

        -1                       as acquisition_campaign_key

),

final as (

    select * from renamed
    union all
    select * from unknown_member

)

select * from final