-- dim_campaign.sql
--
-- Conformed dimension, SCD Type 1 (03_star_schema.md Section 7.8).
-- Grain: one row per campaign, plus one synthetic "No Campaign"
-- member row (campaign_key = -1) -- same -1 convention used by
-- dim_customer's unknown_member, but a distinct meaning: this row
-- represents customers acquired through organic/unpaid channels
-- (no campaign applies, by design), not missing/unknown data.
-- Needed so dim_customer.acquisition_campaign_key can always resolve
-- to a real key with no NULLs, matching the rest of this project's
-- FK convention.
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

real_campaigns as (

    select

        FARM_FINGERPRINT(COALESCE(campaign_id, '-1')) as campaign_key,

        campaign_id,
        campaign_name,
        marketing_platform,
        acquisition_channel_name,
        start_date,
        end_date

    from campaign_grain

),

no_campaign_member as (

    select

        -1                                              as campaign_key,
        'NO_CAMPAIGN'                                    as campaign_id,
        'No Campaign (Organic/Unpaid Channel)'           as campaign_name,
        'N/A'                                             as marketing_platform,
        'N/A'                                             as acquisition_channel_name,
        cast(null as date)                                as start_date,
        cast(null as date)                                as end_date

),

final as (

    select * from real_campaigns
    union all
    select * from no_campaign_member

)

select * from final