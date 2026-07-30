-- fact_marketing_spend.sql
--
-- Transaction fact (03_star_schema.md Section 6.7).
-- Grain: one row per campaign per marketing platform per calendar day
-- -- already matches stg_marketing_spend's grain 1:1, since platform
-- is a constant attribute of campaign_id, not an independent axis.
--
-- stg_marketing_spend is a select * passthrough (project convention --
-- see stg_shipments.sql), so this model reads the raw column names
-- directly (date, spend_sgd, impressions, clicks) and does the
-- star-schema rename here at the mart layer.
--
-- platform_reported_conversions_count is nullable in the star schema
-- spec and intentionally left unpopulated here -- the actual
-- marketing_spend.py generator doesn't produce it. If added to the
-- generator later, wire it through here rather than defaulting it to
-- 0 (0 would falsely imply "measured zero conversions" instead of
-- "not tracked").

with stg_marketing_spend as (

    select * from {{ ref('stg_marketing_spend') }}

),

dim_campaign as (

    select * from {{ ref('dim_campaign') }}

),

final as (

    select

        FARM_FINGERPRINT(COALESCE(s.marketing_spend_id, '-1')) as marketing_spend_key,

        CAST(FORMAT_DATE('%Y%m%d', s.date) AS INT64) as spend_date_key,

        COALESCE(c.campaign_key, -1) as campaign_key,

        s.spend_sgd    as spend_amount,
        s.impressions  as impressions_count,
        s.clicks       as clicks_count,

        CAST(NULL AS INT64) as platform_reported_conversions_count

    from stg_marketing_spend s
    left join dim_campaign c
        on s.campaign_id = c.campaign_id

)

select * from final