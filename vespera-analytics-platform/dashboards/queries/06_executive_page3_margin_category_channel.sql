-- Executive Dashboard, Page 3 — Margin by Category / Channel
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- Grain: category x channel. Both dimensions are present in one
-- table so the same data source powers two different charts — a bar
-- chart using only category_name, and a table using only
-- sales_channel_code. Looker Studio correctly re-sums net_revenue_
-- amount / cogs_amount across the dropped dimension in either case,
-- since both are plain additive sums.
--
-- Gross Margin % calculated field (build in Looker Studio):
--   Gross Margin % = (SUM(net_revenue_amount) - SUM(cogs_amount)) / SUM(net_revenue_amount)

select

    dp.category_name,
    fs.sales_channel_code,

    sum(fs.net_revenue_amount) as net_revenue_amount,
    sum(fs.cogs_amount)        as cogs_amount

from `vespera-analytics-platform.vespera_dw.fact_sales` fs
inner join `vespera-analytics-platform.vespera_dw.dim_date` dd
    on fs.order_date_key = dd.date_key
inner join `vespera-analytics-platform.vespera_dw.dim_product` dp
    on fs.product_key = dp.product_key

where dd.full_date between '2024-01-01' and '2025-12-31'
    and dp.product_id != 'UNKNOWN'

group by 1, 2
