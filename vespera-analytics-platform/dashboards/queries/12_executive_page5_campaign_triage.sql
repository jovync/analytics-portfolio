-- Executive Dashboard, Page 5 — Campaign-Level CAC vs. LTV:CAC (triage table)
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- One row per real campaign (NO_CAMPAIGN synthetic member excluded —
-- it has no spend to evaluate). Pre-sorted worst-to-best by LTV:CAC
-- ratio in the SQL itself, so the table renders in triage order by
-- default without relying on the user to sort it in Looker Studio.
--
-- CAC calculated field (build in Looker Studio):
--   CAC = SUM(total_spend_amount) / SUM(new_customers)
-- LTV:CAC Ratio calculated field:
--   LTV:CAC Ratio = SUM(total_ltv_amount) / SUM(total_spend_amount)

with customer_ltv as (

    select
        customer_key,
        sum(net_revenue_amount) - sum(cogs_amount) as ltv_amount

    from `vespera-analytics-platform.vespera_dw.fact_sales`
    where customer_key != -1
    group by customer_key

),

campaign_customers as (

    select

        dc.acquisition_campaign_key as campaign_key,

        count(distinct dc.customer_key)  as new_customers,
        sum(coalesce(cl.ltv_amount, 0))  as total_ltv_amount

    from `vespera-analytics-platform.vespera_dw.dim_customer` dc
    left join customer_ltv cl
        on dc.customer_key = cl.customer_key

    where dc.customer_id != 'UNKNOWN'
    group by 1

),

campaign_spend as (

    select
        campaign_key,
        sum(spend_amount) as total_spend_amount

    from `vespera-analytics-platform.vespera_dw.fact_marketing_spend`
    group by campaign_key

)

select

    dcamp.campaign_name,
    dcamp.acquisition_channel_name,
    dcamp.marketing_platform,

    coalesce(cs.total_spend_amount, 0) as total_spend_amount,
    coalesce(cc.new_customers, 0)      as new_customers,
    coalesce(cc.total_ltv_amount, 0)   as total_ltv_amount

from `vespera-analytics-platform.vespera_dw.dim_campaign` dcamp
left join campaign_spend cs
    on dcamp.campaign_key = cs.campaign_key
left join campaign_customers cc
    on dcamp.campaign_key = cc.campaign_key

where dcamp.campaign_id != 'NO_CAMPAIGN'

order by safe_divide(
    coalesce(cc.total_ltv_amount, 0),
    nullif(coalesce(cs.total_spend_amount, 0), 0)
) asc
