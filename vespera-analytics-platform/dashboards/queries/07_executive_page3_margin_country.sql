-- Executive Dashboard, Page 3 — Margin by Country (geo map)
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- Uses dim_customer.customer_country, not fact_sales' warehouse
-- location — this is "which country the customer is in," matching
-- the spec's "Gross Margin % by Country" geo map intent (customer
-- geography, not fulfillment geography). If you actually want
-- fulfillment-location margin instead, that's a different join
-- through dim_warehouse, not this query.
--
-- Gross Margin % calculated field (build in Looker Studio):
--   Gross Margin % = (SUM(net_revenue_amount) - SUM(cogs_amount)) / SUM(net_revenue_amount)
--
-- Looker Studio geo charts need a recognized geography field type —
-- set customer_country's Type to "Country" (or "Country Code" if the
-- values are ISO codes, not full names) in the field editor, or the
-- map won't render.

select

    dc.customer_country,

    sum(fs.net_revenue_amount) as net_revenue_amount,
    sum(fs.cogs_amount)        as cogs_amount

from `vespera-analytics-platform.vespera_dw.fact_sales` fs
inner join `vespera-analytics-platform.vespera_dw.dim_date` dd
    on fs.order_date_key = dd.date_key
inner join `vespera-analytics-platform.vespera_dw.dim_customer` dc
    on fs.customer_key = dc.customer_key

where dd.full_date between '2024-01-01' and '2025-12-31'
    and dc.customer_id != 'UNKNOWN'

group by 1
