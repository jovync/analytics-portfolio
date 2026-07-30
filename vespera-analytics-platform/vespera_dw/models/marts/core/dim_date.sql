-- Generated calendar dimension — no raw source table backs this one.
-- Range padded beyond the simulation window (2024-01-01 to 2025-12-31)
-- to safely cover return dates (up to +30 days past a delivery) and
-- purchase order expected-delivery dates that can land after
-- SIMULATION_END_DATE for "In Transit" POs.
--
-- Fiscal year/quarter/month assumed identical to calendar — no
-- evidence anywhere in the source docs of a non-calendar fiscal year.
-- holiday_flag is a simplified heuristic (New Year's Day, Christmas,
-- and the SEA e-commerce flash-sale dates called out in
-- config.py's SEASONALITY_MULTIPLIERS comments: 9/9, 10/10, 11/11,
-- 12/12) — not a real public-holiday calendar per country.

with date_spine as (

    select calendar_date
    from unnest(
        generate_date_array('2023-01-01', '2026-12-31', interval 1 day)
    ) as calendar_date

),

enriched as (

    select
        cast(format_date('%Y%m%d', calendar_date) as int64) as date_key,
        calendar_date                                        as full_date,

        extract(dayofweek from calendar_date)                as day_of_week_number,
        format_date('%A', calendar_date)                     as day_name,
        extract(dayofweek from calendar_date) in (1, 7)       as is_weekend_flag,

        extract(isoweek from calendar_date)                  as week_number,
        extract(month from calendar_date)                    as calendar_month_number,
        format_date('%B', calendar_date)                      as month_name,
        extract(quarter from calendar_date)                  as calendar_quarter_number,
        extract(year from calendar_date)                     as calendar_year_number,

        -- fiscal = calendar (see header note)
        extract(year from calendar_date)                     as fiscal_year_number,
        extract(quarter from calendar_date)                  as fiscal_quarter_number,
        extract(month from calendar_date)                    as fiscal_month_number,

        (
            (extract(month from calendar_date) = 1  and extract(day from calendar_date) = 1)
            or (extract(month from calendar_date) = 12 and extract(day from calendar_date) = 25)
            or (extract(month from calendar_date) = 9  and extract(day from calendar_date) = 9)
            or (extract(month from calendar_date) = 10 and extract(day from calendar_date) = 10)
            or (extract(month from calendar_date) = 11 and extract(day from calendar_date) = 11)
            or (extract(month from calendar_date) = 12 and extract(day from calendar_date) = 12)
        )                                                     as holiday_flag

    from date_spine

)

select * from enriched
