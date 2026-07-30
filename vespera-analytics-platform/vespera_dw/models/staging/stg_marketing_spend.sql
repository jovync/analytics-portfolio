-- Daily spend by campaign, 4 paid channels only (per the handoff:
-- first-touch, customer-level attribution — no per-order attribution
-- exists, so this won't join cleanly to fact_sales at the order grain).
-- Column list not independently verified against the live table yet —
-- see verification note in stg_shipments.sql.

with source as (

    select * from {{ source('vespera_raw', 'raw_marketing_spend') }}

),

renamed as (

    select *

    from source

)

select * from renamed
