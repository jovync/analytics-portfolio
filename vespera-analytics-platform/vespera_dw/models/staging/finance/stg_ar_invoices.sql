-- Lighter-touch pass-through, matching the convention in
-- stg_shipments.sql for newly-loaded sources. Unlike
-- raw_acquisition_attribution, this one was loaded with an explicit
-- --schema (not autodetect), so column types are already correct --
-- still keeping select * for now per project convention, but this
-- one doesn't carry the same "unverified" risk.
--
-- Columns per python/generators/ar_invoices.py: invoice_id, order_id,
-- customer_id, payment_terms_code, invoice_date, due_date,
-- invoice_amount, amount_paid, payment_date (nullable -- null means
-- still open, not missing data), invoice_status.

with source as (

    select * from {{ source('vespera_raw', 'raw_ar_invoices') }}

),

renamed as (

    select *

    from source

)

select * from renamed
