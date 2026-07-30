-- Lighter-touch pass-through: shipment_status is derived from
-- order_status at generation time (not independently sampled), so
-- treat it as authoritative rather than re-deriving it here.
--
-- Full column list not independently verified against the live
-- table yet — after first `dbt run`, diff this SELECT * against
-- INFORMATION_SCHEMA.COLUMNS and switch to an explicit column list
-- (matching the style of the other staging models) once confirmed.

with source as (

    select * from {{ source('vespera_raw', 'raw_shipments') }}

),

renamed as (

    select *

    from source

)

select * from renamed
