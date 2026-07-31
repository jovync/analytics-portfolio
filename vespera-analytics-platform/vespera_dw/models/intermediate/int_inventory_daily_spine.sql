-- One row per (invoice, day) -- from invoice_date through the
-- earlier of payment_date or the simulation end date (2025-12-31,
-- same hardcoded bound used in int_inventory_daily_spine.sql).
-- Still-open invoices (payment_date is null) run through simulation
-- end; paid/partially-paid invoices stop at their payment_date --
-- no value in snapshotting a $0-balance invoice indefinitely, so the
-- window naturally closes there rather than needing a separate
-- zero-balance filter downstream.
--
-- Added in the v1.2 KPI Framework <-> Star Schema reconciliation to
-- close the DSO data gap -- see docs/06_kpi_schema_reconciliation.md.
--
-- Expect roughly 3,324 invoices x up to ~60 days each (payment terms
-- cap at NET60) -- on the order of ~100-150K rows, much smaller than
-- the inventory spine since invoice windows are short-lived by
-- design, not a bug if the row count looks small by comparison.

with stg_ar_invoices as (

    select * from {{ ref('stg_ar_invoices') }}

),

dim_date as (

    select * from {{ ref('dim_date') }}

),

bounded_invoices as (

    select

        invoice_id,
        order_id,
        customer_id,
        payment_terms_code,
        invoice_date,
        due_date,
        invoice_amount,
        amount_paid,
        payment_date,
        invoice_status,

        invoice_date as window_start,

        least(coalesce(payment_date, date('2025-12-31')), date('2025-12-31'))
            as window_end

    from stg_ar_invoices

),

spine as (

    select

        bi.invoice_id,
        bi.order_id,
        bi.customer_id,
        bi.payment_terms_code,
        bi.invoice_date,
        bi.due_date,
        bi.invoice_amount,
        bi.amount_paid,
        bi.payment_date,
        bi.invoice_status,
        d.full_date as snapshot_date

    from bounded_invoices bi
    inner join dim_date d
        on d.full_date between bi.window_start and bi.window_end

)

select * from spine