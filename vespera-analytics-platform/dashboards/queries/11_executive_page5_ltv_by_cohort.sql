-- Executive Dashboard, Page 5 — LTV by Customer Cohort
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- Cohort = the month a customer signed up (customer_since), not the
-- month they were acquired via a specific campaign — this shows
-- "how much has each signup cohort generated in lifetime margin so
-- far," which naturally trends lower for more recent cohorts since
-- they've had less time to accumulate orders. That's expected
-- cohort-curve behavior, not a bug — a Jan 2024 cohort has had two
-- full years to order repeatedly; a Nov 2025 cohort has had weeks.
--
-- Includes ALL customers (not just paid-channel-attributed ones),
-- unlike the channel-level LTV:CAC queries — this chart is about
-- cohort value overall, not spend efficiency specifically.
--
-- LTV per customer calculated field (build in Looker Studio):
--   LTV per customer = SUM(total_ltv_amount) / SUM(customers)

with customer_ltv as (

    select
        customer_key,
        sum(net_revenue_amount) - sum(cogs_amount) as ltv_amount

    from `vespera-analytics-platform.vespera_dw.fact_sales`
    where customer_key != -1
    group by customer_key

)

select

    date_trunc(dc.customer_since, month) as cohort_month,

    count(distinct dc.customer_key)            as customers,
    sum(coalesce(cl.ltv_amount, 0))             as total_ltv_amount

from `vespera-analytics-platform.vespera_dw.dim_customer` dc
left join customer_ltv cl
    on dc.customer_key = cl.customer_key

where dc.customer_id != 'UNKNOWN'
group by 1
order by 1
