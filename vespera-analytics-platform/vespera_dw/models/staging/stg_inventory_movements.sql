-- Signed-quantity ledger: Customer Sale (negative), Customer Return
-- (positive), Inbound Purchase (positive), per the handoff. Column
-- list not independently verified against the live table yet — see
-- verification note in stg_shipments.sql.

with source as (

    select * from {{ source('vespera_raw', 'raw_inventory_movements') }}

),

renamed as (

    select *

    from source

)

select * from renamed
