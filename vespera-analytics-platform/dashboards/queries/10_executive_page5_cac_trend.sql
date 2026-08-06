-- Executive Dashboard, Page 5 — CAC Trend by Acquisition Channel
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- Monthly grain, not daily — daily CAC would be mostly undefined
-- (zero new customers on most individual days per channel), so a
-- month is the smallest grain that gives a stable trend line.
--
-- FULL OUTER JOIN handles months where a channel had spend but zero
-- attributed signups, or vice versa (shouldn't happen in practice
-- since spend without any attribution would mean 100% wasted budget,
-- but the join is defensive either way).
--
-- CAC calculated field (build in Looker Studio):
--   CAC = SUM(spend_amount) / SUM(new_customers)

with campaign_channel as (

    select
        campaign_key,
        acquisition_channel_name,
        marketing_platform

    from `vespera-analytics-platform.vespera_dw.dim_campaign`
    where campaign_id != 'NO_CAMPAIGN'

),

monthly_spend as (

    select

        date_trunc(dd.full_date, month) as report_month,
        cc.acquisition_channel_name,

        sum(fms.spend_amount) as spend_amount

    from `vespera-analytics-platform.vespera_dw.fact_marketing_spend` fms
    inner join `vespera-analytics-platform.vespera_dw.dim_date` dd
        on fms.spend_date_key = dd.date_key
    inner join campaign_channel cc
        on fms.campaign_key = cc.campaign_key

    group by 1, 2

),

monthly_new_customers as (

    select

        date_trunc(dc.customer_since, month) as report_month,
        cc.acquisition_channel_name,

        count(distinct dc.customer_key) as new_customers

    from `vespera-analytics-platform.vespera_dw.dim_customer` dc
    inner join campaign_channel cc
        on dc.acquisition_campaign_key = cc.campaign_key

    where dc.customer_id != 'UNKNOWN'
    group by 1, 2

)

select

    coalesce(s.report_month, n.report_month)                       as report_month,
    coalesce(s.acquisition_channel_name, n.acquisition_channel_name) as acquisition_channel_name,

    coalesce(s.spend_amount, 0)   as spend_amount,
    coalesce(n.new_customers, 0)  as new_customers

from monthly_spend s
full outer join monthly_new_customers n
    on s.report_month = n.report_month
    and s.acquisition_channel_name = n.acquisition_channel_name

order by 1, 2
