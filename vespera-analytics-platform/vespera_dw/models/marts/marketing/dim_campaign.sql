-- dim_campaign.sql
--
-- Conformed dimension, SCD Type 1 (03_star_schema.md Section 7.8).
-- Grain: one row per campaign.
--
-- stg_marketing_spend is a select * passthrough (project convention --
-- see stg_shipments.sql), so this model reads the raw column names
-- directly (channel, platform, date, spend_sgd) and does the
-- star-schema rename here at the mart layer instead.
--
-- start_date/end_date are derived as min/max(date) rather than
-- sourced from a separate campaign calendar table, since
-- marketing_spend.py's campaign builder is a private helper with no
-- separate export.
--
-- NOTE: 03_star_schema.md's original dim_campaign spec included an
-- objective_type column. The actual marketing_spend.py generator
-- doesn't produce this field, so it's omitted here rather than
-- faked. Follow-up: update 03_star_schema.md and 05_data_dictionary.md
-- to drop objective_type (or mark it explicitly unsourced) so the
-- docs match what's actually built.

with stg_marketing_spend as (

    select * from {{ ref('stg_marketing_spend') }}

),

campaign_grain as (

    select

        campaign_id,

        -- campaign_name, channel, platform are constant per
        -- campaign_id in the source -- any_value is safe here, not
        -- an arbitrary pick across differing values.
        any_value(campaign_name) as campaign_name,
        any_value(channel)       as acquisition_channel_name,
        any_value(platform)      as marketing_platform,

        min(date) as start_date,
        max(date) as end_date

    from stg_marketing_spend
    group by campaign_id

),

final as (

    select

        FARM_FINGERPRINT(COALESCE(campaign_id, '-1')) as campaign_key,

        campaign_id,
        campaign_name,
        marketing_platform,
        acquisition_channel_name,
        start_date,
        end_date

    from campaign_grain

)

select * from final