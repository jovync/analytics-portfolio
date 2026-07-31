-- Executive Dashboard, Page 2 — Top SKUs by Net Revenue
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- Powers a "Table with bars" chart (Insert > Table > Table with bars)
-- — the native Looker Studio substitute for a sparkline, since true
-- inline sparklines aren't natively supported. Sort descending on
-- net_revenue_amount and set the table's "Rows per page" or a Top N
-- filter to 10 for the "Top 10" framing from the design spec.
--
-- Scoped to the same 2024-01-01 to 2025-12-31 window as the rest of
-- the Executive Dashboard for consistency, not just last-90-days —
-- adjust the WHERE clause if you want this table to respect the
-- report-level date range control instead of a fixed window.

select

    dp.product_name,
    dp.sku_code,
    dp.category_name,
    dp.brand_name,

    sum(fs.net_revenue_amount) as net_revenue_amount,
    sum(fs.quantity_ordered)   as units_sold,

    safe_divide(sum(fs.net_revenue_amount), sum(fs.quantity_ordered))
        as avg_selling_price

from `vespera-analytics-platform.vespera_dw.fact_sales` fs
inner join `vespera-analytics-platform.vespera_dw.dim_date` dd
    on fs.order_date_key = dd.date_key
inner join `vespera-analytics-platform.vespera_dw.dim_product` dp
    on fs.product_key = dp.product_key

where dd.full_date between '2024-01-01' and '2025-12-31'
    and dp.product_id != 'UNKNOWN'

group by 1, 2, 3, 4

order by net_revenue_amount desc
