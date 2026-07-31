-- Executive Dashboard, Page 2 — Revenue & Growth Trend
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- Powers TWO visuals from one data source:
--   1. Line chart: report_date (dim) x net_revenue_amount (metric),
--      breakdown dimension = sales_channel_code
--   2. Bar chart: sales_channel_code (dim) x AOV (calculated field)
--
-- Same additive-components discipline as Page 1: completed_orders is
-- returned raw, not pre-divided, so AOV = SUM(net_revenue_amount) /
-- SUM(completed_orders) aggregates correctly at any grouping level.

select

    dd.full_date as report_date,
    fs.sales_channel_code,

    sum(fs.net_revenue_amount) as net_revenue_amount,

    count(distinct case
        when fs.fulfillment_status != 'Cancelled' then fs.order_number
    end) as completed_orders

from `vespera-analytics-platform.vespera_dw.fact_sales` fs
inner join `vespera-analytics-platform.vespera_dw.dim_date` dd
    on fs.order_date_key = dd.date_key

where dd.full_date between '2024-01-01' and '2025-12-31'

group by 1, 2

order by 1, 2
