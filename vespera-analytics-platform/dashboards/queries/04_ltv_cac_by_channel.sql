-- Executive Dashboard Page 1 (LTV:CAC scorecard) and Marketing
-- Dashboard Page 3 (LTV vs. CAC by channel) — same query serves both.
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- One row per acquisition channel (Facebook Ads, Instagram, TikTok,
-- Email Campaign). Organic/Referral customers are excluded entirely
-- (dim_campaign's 'NO_CAMPAIGN' member filtered out) — CAC is
-- undefined without a spend numerator, and including them with a
-- zero-cost denominator would produce a meaningless infinite ratio,
-- not a real "organic is great" signal.
--
-- LTV here is CUMULATIVE lifetime value as of the end of the
-- simulation window (2025-12-31), not month-scoped — this is a
-- simplification of the KPI Framework's monthly cadence. A true
-- monthly LTV:CAC trend would need LTV computed as-of each month's
-- cohort age, which is a meaningfully bigger modeling exercise; this
-- gives you the channel-level "which acquisition channels are
-- actually profitable" read, which is what the bar chart / scatter
-- plot in the Marketing Dashboard spec actually needs.
--
-- Same additive-components discipline as every other query here:
-- total_spend_amount, attributed_customers, and total_ltv_amount are
-- all raw sums. Build these as calculated fields in Looker Studio,
-- not pre-divided in SQL:
--   CAC              = SUM(total_spend_amount) / SUM(attributed_customers)
--   LTV per customer = SUM(total_ltv_amount) / SUM(attributed_customers)
--   LTV:CAC Ratio    = SUM(total_ltv_amount) / SUM(total_spend_amount)
--                      (customers cancel out algebraically — this
--                      simplification is intentional and correct)

with customer_ltv as (

    select
        customer_key,
        sum(net_revenue_amount) - sum(cogs_amount) as ltv_amount

    from `vespera-analytics-platform.vespera_dw.fact_sales`
    where customer_key != -1
    group by customer_key

),

customer_attribution as (

    select
        dc.customer_key,
        dcamp.acquisition_channel_name,
        dcamp.marketing_platform,
        coalesce(cl.ltv_amount, 0) as ltv_amount

    from `vespera-analytics-platform.vespera_dw.dim_customer` dc
    inner join `vespera-analytics-platform.vespera_dw.dim_campaign` dcamp
        on dc.acquisition_campaign_key = dcamp.campaign_key
    left join customer_ltv cl
        on dc.customer_key = cl.customer_key

    where dc.customer_id != 'UNKNOWN'
        and dcamp.campaign_id != 'NO_CAMPAIGN'

),

channel_ltv as (

    select
        acquisition_channel_name,
        marketing_platform,
        count(distinct customer_key) as attributed_customers,
        sum(ltv_amount)              as total_ltv_amount

    from customer_attribution
    group by 1, 2

),

channel_spend as (

    select
        dcamp.acquisition_channel_name,
        dcamp.marketing_platform,
        sum(fms.spend_amount) as total_spend_amount

    from `vespera-analytics-platform.vespera_dw.fact_marketing_spend` fms
    inner join `vespera-analytics-platform.vespera_dw.dim_campaign` dcamp
        on fms.campaign_key = dcamp.campaign_key

    where dcamp.campaign_id != 'NO_CAMPAIGN'
    group by 1, 2

)

select

    cl.acquisition_channel_name,
    cl.marketing_platform,

    coalesce(cs.total_spend_amount, 0) as total_spend_amount,
    cl.attributed_customers,
    cl.total_ltv_amount

from channel_ltv cl
left join channel_spend cs
    on cl.acquisition_channel_name = cs.acquisition_channel_name
    and cl.marketing_platform = cs.marketing_platform

order by cl.total_ltv_amount desc
