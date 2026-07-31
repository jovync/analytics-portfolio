-- Executive Dashboard, Page 3 -- DSO scorecard component
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- CORRECTED VERSION -- the original used AVG(open_balance_amount)
-- per day, which gives the average SIZE of a single open invoice,
-- not the total outstanding AR that day. DSO's numerator needs
-- total AR exposure, not typical invoice size. Fixed by SUM-ing
-- open_balance_amount within each day (total AR that day), then
-- treating THAT as the semi-additive snapshot metric across days.
--
-- Reuse the Page 1 data source for the Net Revenue / Gross Margin % /
-- COGS scorecards on this page -- same underlying fact_sales columns,
-- no need to duplicate that query.
--
-- daily_total_ar is a daily SNAPSHOT total (same category as Page 1's
-- active_skus/stockout_skus) -- in Looker Studio, set this field's
-- default aggregation to AVERAGE, not SUM. Averaging the daily totals
-- across the period gives "average daily AR exposure," which is the
-- correct DSO numerator. Summing it would double-count every open
-- invoice on every day it stayed open.
--
-- credit_net_revenue_amount is a normal additive SUM -- orders on
-- credit terms only (payment_terms_code != 'DUE_ON_RECEIPT'), DSO's
-- denominator per the KPI Framework formula.
--
-- DSO calculated field (build in Looker Studio):
--   DSO = AVG(daily_total_ar) / (SUM(credit_net_revenue_amount) / COUNT_DISTINCT(report_date))
-- This generalizes the KPI Framework's "trailing 30 days / 30"
-- formula to whatever date range is currently selected, rather than
-- hardcoding 30 -- COUNT_DISTINCT(report_date) is the actual number
-- of days in whatever range the user has filtered to.

with date_spine as (

    select
        full_date as report_date,
        date_key

    from `vespera-analytics-platform.vespera_dw.dim_date`
    where full_date between '2024-01-01' and '2025-12-31'

),

daily_total_ar as (

    select
        snapshot_date_key,
        sum(open_balance_amount) as daily_total_ar

    from `vespera-analytics-platform.vespera_dw.fact_ar_aging_daily`
    group by snapshot_date_key

),

daily_credit_sales as (

    select
        order_date_key,
        sum(net_revenue_amount) as credit_net_revenue_amount

    from `vespera-analytics-platform.vespera_dw.fact_sales`
    where payment_terms_code != 'DUE_ON_RECEIPT'
    group by order_date_key

)

select

    ds.report_date,
    coalesce(ar.daily_total_ar, 0)             as daily_total_ar,
    coalesce(cs.credit_net_revenue_amount, 0)  as credit_net_revenue_amount

from date_spine ds
left join daily_total_ar ar
    on ds.date_key = ar.snapshot_date_key
left join daily_credit_sales cs
    on ds.date_key = cs.order_date_key

order by ds.report_date
