-- Lighter-touch pass-through, matching the convention in
-- stg_shipments.sql and stg_marketing_spend.sql for newly-loaded
-- sources: verify against the live table before switching to an
-- explicit column list.
--
-- Full column list not independently verified against the live
-- table yet -- after first `dbt run`, diff this SELECT * against
-- INFORMATION_SCHEMA.COLUMNS and switch to an explicit column list
-- (matching the style of the other staging models) once confirmed.
--
-- Expected columns per python/generators/acquisition_attribution.py:
-- customer_id, acquisition_campaign_id (nullable -- unpaid-channel
-- customers have no attribution by design, not a data quality issue).

with source as (

    select * from {{ source('vespera_raw', 'raw_acquisition_attribution') }}

),

renamed as (

    select *

    from source

)

select * from renamed
