-- Executive Dashboard, Page 4 — AOV & Return Rate by Channel Class
-- Paste into Looker Studio: Add Data > BigQuery > Custom Query
--
-- Unblocked by adding order_number to fact_returns.sql. order_channel
-- maps each order to its Channel Class ONCE (SELECT DISTINCT on
-- order_number), then both fact_sales and fact_returns join to it by
-- order_number — avoids fan-out, since fact_sales is line-item grain
-- and would otherwise produce duplicate channel mappings per order.
--
-- Same Channel Class mapping as query 08 — keep both in sync if the
-- channel list ever changes.
--
-- AOV calculated field (build in Looker Studio):
--   AOV = SUM(net_revenue_amount) / SUM(completed_orders)
-- Return Rate calculated field:
--   Return Rate = SUM(returned_units) / SUM(sold_units)

with order_channel as (

    select distinct

        order_number as order_id,

        case sales_channel_code
            when 'Shopify' then 'Web'
            when 'Retail'  then 'Retail Boutique'
            when 'Shopee'  then 'Marketplace'
            when 'Lazada'  then 'Marketplace'
            else 'Other'
        end as channel_class

    from `vespera-analytics-platform.vespera_dw.fact_sales`

),

sales_by_class as (

    select

        oc.channel_class,

        sum(fs.net_revenue_amount) as net_revenue_amount,
        sum(fs.quantity_ordered)   as sold_units,

        count(distinct case
            when fs.fulfillment_status != 'Cancelled' then fs.order_number
        end) as completed_orders

    from `vespera-analytics-platform.vespera_dw.fact_sales` fs
    inner join `vespera-analytics-platform.vespera_dw.dim_date` dd
        on fs.order_date_key = dd.date_key
    inner join order_channel oc
        on fs.order_number = oc.order_id

    where dd.full_date between '2024-01-01' and '2025-12-31'
    group by 1

),

returns_by_class as (

    select

        oc.channel_class,
        sum(fr.returned_quantity) as returned_units

    from `vespera-analytics-platform.vespera_dw.fact_returns` fr
    inner join `vespera-analytics-platform.vespera_dw.dim_date` dd
        on fr.return_date_key = dd.date_key
    inner join order_channel oc
        on fr.order_number = oc.order_id

    where dd.full_date between '2024-01-01' and '2025-12-31'
    group by 1

)

select

    s.channel_class,
    s.net_revenue_amount,
    s.sold_units,
    s.completed_orders,

    coalesce(r.returned_units, 0) as returned_units

from sales_by_class s
left join returns_by_class r
    on s.channel_class = r.channel_class
