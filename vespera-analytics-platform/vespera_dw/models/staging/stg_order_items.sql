-- NOTE: tax_amount and commission_amount are per the project handoff
-- ("Fixed missing tax/commission/refund/restocking fee fields per KPI
-- framework cross-check") but weren't visible in the last generator
-- snapshot I could inspect. If this model fails to compile on first
-- `dbt run`, check `raw_order_items` columns via:
--   SELECT column_name FROM vespera_dw_raw.INFORMATION_SCHEMA.COLUMNS
--   WHERE table_name = 'raw_order_items'
-- and adjust the two lines below accordingly.

with source as (

    select * from {{ source('vespera_raw', 'raw_order_items') }}

),

renamed as (

    select
        order_item_id,
        order_id,
        product_id,
        warehouse_id,
        quantity,
        unit_price,
        discount_pct,
        gross_sales,
        discount_amount,
        net_sales,
        tax_amount,
        commission_amount

    from source

)

select * from renamed
