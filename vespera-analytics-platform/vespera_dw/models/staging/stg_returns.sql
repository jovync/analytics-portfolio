-- CONFIRMED against BigQuery INFORMATION_SCHEMA.COLUMNS (2026-07-30):
-- raw_returns does NOT have refunded_amount or restocking_fee_amount.
-- Only the 10 columns below exist. fact_returns in 03_star_schema.md /
-- 05_data_dictionary.md still lists those two as measures — that's a
-- documentation/data divergence to resolve before building fact_returns
-- (either derive refund/fee in a later dbt layer from order_items +
-- disposition, or update the docs to drop them, matching how dim_store
-- was reconciled earlier). Not fixed here — flagging for that pass.

with source as (

    select * from {{ source('vespera_raw', 'raw_returns') }}

),

renamed as (

    select
        return_id,
        order_id,
        order_item_id,
        shipment_id,
        product_id,
        warehouse_id,
        return_date,
        quantity                   as returned_quantity,
        return_reason,
        disposition                as disposition_code

    from source

)

select * from renamed