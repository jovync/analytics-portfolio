-- Executive Dashboard, Page 4 — Revenue Mix by Channel Class
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- Channel Class is a business grouping not present as a column
-- anywhere in the star schema — built here via CASE WHEN on the
-- four real sales_channel_code values (confirmed from your actual
-- CHANNELS config: Shopify, Shopee, Lazada, Retail). If a fifth
-- channel ever gets added to that config, this mapping needs a
-- matching update or it'll silently bucket the new channel as
-- 'Other'.
--
-- Monthly grain for a mix trend over time, not a single point-in-
-- time bar — use as a 100%-stacked bar or area chart to show how the
-- channel mix shifts month to month.

select

    date_trunc(dd.full_date, month) as report_month,

    case fs.sales_channel_code
        when 'Shopify' then 'Web'
        when 'Retail'  then 'Retail Boutique'
        when 'Shopee'  then 'Marketplace'
        when 'Lazada'  then 'Marketplace'
        else 'Other'
    end as channel_class,

    sum(fs.net_revenue_amount) as net_revenue_amount

from `vespera-analytics-platform.vespera_dw.fact_sales` fs
inner join `vespera-analytics-platform.vespera_dw.dim_date` dd
    on fs.order_date_key = dd.date_key

where dd.full_date between '2024-01-01' and '2025-12-31'

group by 1, 2
order by 1, 2
