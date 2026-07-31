-- fact_ar_aging_daily.sql
--
-- Periodic snapshot fact (03_star_schema.md Section 6.6).
-- Grain: one row per open customer invoice per calendar day.
-- Built on int_ar_invoice_daily_spine.sql -- same pattern as
-- fact_inventory_daily building on int_inventory_daily_spine.sql.
--
-- open_balance_amount convention: on payment_date itself, the
-- balance already reflects post-payment (invoice_amount - amount_paid)
-- rather than the pre-payment amount -- i.e. payment is treated as
-- posting at the start of that day, not the end. A simplification,
-- but a defensible and documented one.
--
-- Aging buckets classify days_outstanding as of each snapshot day
-- (not just the final outcome), so a snapshot from early in an
-- invoice's life correctly lands in the 0-30 bucket even if that
-- same invoice is 90+ days overdue by the end of the simulation.
--
-- Added in the v1.2 KPI Framework <-> Star Schema reconciliation to
-- close the DSO data gap -- see docs/06_kpi_schema_reconciliation.md.

with int_ar_invoice_daily_spine as (

    select * from {{ ref('int_ar_invoice_daily_spine') }}

),

dim_customer as (

    select * from {{ ref('dim_customer') }}
    where customer_id != 'UNKNOWN'

),

with_balance as (

    select

        s.*,

        case
            when s.payment_date is null or s.snapshot_date < s.payment_date
                then s.invoice_amount
            else s.invoice_amount - s.amount_paid
        end as open_balance_amount,

        date_diff(s.snapshot_date, s.invoice_date, day) as days_outstanding

    from int_ar_invoice_daily_spine s

),

final as (

    select

        FARM_FINGERPRINT(
            CONCAT(wb.invoice_id, '-', CAST(wb.snapshot_date AS STRING))
        ) as ar_snapshot_key,

        CAST(FORMAT_DATE('%Y%m%d', wb.snapshot_date) AS INT64)
            as snapshot_date_key,

        COALESCE(dc.customer_key, -1) as customer_key,

        wb.invoice_id as invoice_number,
        wb.payment_terms_code,

        wb.invoice_amount,
        wb.open_balance_amount,
        wb.days_outstanding,

        case when wb.days_outstanding between 0 and 30
            then wb.open_balance_amount else 0
        end as aging_bucket_0_30_amount,

        case when wb.days_outstanding between 31 and 60
            then wb.open_balance_amount else 0
        end as aging_bucket_31_60_amount,

        case when wb.days_outstanding between 61 and 90
            then wb.open_balance_amount else 0
        end as aging_bucket_61_90_amount,

        case when wb.days_outstanding > 90
            then wb.open_balance_amount else 0
        end as aging_bucket_90_plus_amount

    from with_balance wb
    left join dim_customer dc
        on wb.customer_id = dc.customer_id

)

select * from final
