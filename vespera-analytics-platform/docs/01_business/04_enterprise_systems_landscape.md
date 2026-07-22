# Enterprise Systems Landscape

## Purpose

The Enterprise Systems Landscape documents the operational systems that generate data across **Vespera Lifestyle Group**. Each system supports one or more core business processes and serves as a **system of record** for the enterprise analytics platform.

By documenting system ownership, operational responsibilities, data generation patterns, synchronization frequencies, and integration challenges, this document establishes the architectural foundation for enterprise data governance, ETL/ELT pipeline design, and standardized business reporting.

---

# Enterprise Analytics Architecture

```
                  +-----------------------------------+
                  |       Executive Dashboards        |
                  |          (Looker Studio)          |
                  +-----------------▲-----------------+
                                    │
                  +-----------------+-----------------+
                  |     Semantic Analytics Layer      |
                  |   Enterprise KPIs & Metrics       |
                  +-----------------▲-----------------+
                                    │
                  +-----------------+-----------------+
                  |     Enterprise Data Warehouse     |
                  |            (BigQuery)             |
                  +-----------------▲-----------------+
                                    │
                  +-----------------+-----------------+
                  |     Transformation Layer          |
                  |               (dbt)               |
                  +-----------------▲-----------------+
                                    │
                  +-----------------+-----------------+
                  |    ETL / Orchestration Layer      |
                  |      (Python / Airflow)           |
                  +-----------------▲-----------------+
                                    │
────────────────────────────────────────────────────────────────────────────

                      OPERATIONAL SOURCE SYSTEMS

 ERP / Finance      Omnichannel POS      E-Commerce      Warehouse Management
   NetSuite           Shopify POS        Shopify Plus        Logiwa WMS

 Manufacturing      CRM & Support      Marketing       Marketplace Platforms
 Custom MES           Zendesk       Meta / Google / TikTok   Shopee / Lazada
```

---

# Source Systems Inventory & Governance

The table below catalogs the operational systems that feed the Vespera Lifestyle Group enterprise analytics platform. Each system is mapped to its business owner, technology platform, synchronization frequency, and primary integration challenges.

| Core Business Process | Source System | Technology Platform | Business Owner | Data Generated | Refresh Frequency | Primary Integration Challenge |
|----------------------|---------------|---------------------|----------------|----------------|-------------------|-------------------------------|
| **Product Lifecycle** | ERP / Product Information Management | Oracle NetSuite | Merchandising Director | SKU master records, product hierarchy, BOM, regional pricing | Daily Batch | Duplicate supplier records and inconsistent SKU naming across sales channels |
| **Sourcing & Manufacturing** | Manufacturing Execution System | Custom Manufacturing System | Production Manager | Work-in-Progress (WIP), production batches, quality inspections, defect codes | Event Driven | Semi-manual factory logging results in incomplete production and quality records |
| **Inventory Movement** | Warehouse Management System | Logiwa WMS | VP of Supply Chain | Inventory balances, warehouse locations, transfer orders, pick/pack events | Every 4 Hours | Inventory synchronization delays create stock discrepancies between warehouse and e-commerce channels |
| **Retail Sales** | Point of Sale | Shopify POS | Retail Operations Manager | Store transactions, cashier sessions, payment methods, register reconciliation | Near Real-Time | End-of-day reconciliation creates temporary reporting delays |
| **Online Sales** | E-Commerce Platform | Shopify Plus | E-Commerce Lead | Online orders, customer profiles, checkout events, discount codes | Event Driven | Refunds and cancellations arrive asynchronously through webhooks |
| **Marketplace Sales** | Marketplace Platforms | Shopee & Lazada APIs | Marketplace Specialist | Marketplace orders, commissions, vouchers, shipping subsidies | Weekly Batch | Manual CSV exports require schema normalization and currency reconciliation |
| **Reverse Logistics** | Customer Support & POS | Zendesk & Shopify POS | Customer Experience Lead | Return requests, inspection outcomes, refunds, customer complaints | Daily Batch | Return reason descriptions lack standardization across channels |
| **Customer Engagement** | Marketing Platforms & CRM | Meta Ads, Google Ads, TikTok Ads, Klaviyo | Marketing Director | Campaign spend, impressions, clicks, conversions, email engagement | Daily Batch | Marketing performance is disconnected from ERP profitability and return data |
| **Financial Performance** | ERP & General Ledger | Oracle NetSuite | Head of Finance | Journal entries, revenue recognition, COGS, financial statements | Month-End Close | Marketplace settlements require extensive manual reconciliation before financial close |

---

# Integration Principles

The enterprise analytics platform follows a set of architectural principles designed to ensure scalability, consistency, and trust across all reporting and analytical workloads.

- **Single Source of Truth** – Enterprise KPIs are calculated within the analytics platform rather than individual operational systems.
- **Business Logic Centralization** – Metric definitions, transformations, and calculations are standardized to eliminate conflicting reports across departments.
- **Incremental Data Processing** – Data pipelines load only new or modified records whenever possible to improve efficiency and reduce processing time.
- **Data Quality by Design** – Validation, deduplication, and business rule enforcement occur before data reaches reporting layers.
- **Loose System Coupling** – Operational applications remain independent while exposing standardized datasets to the enterprise analytics platform.

---

# Enterprise Data Lifecycle

Operational data flows sequentially through the organization's business processes before being transformed into trusted enterprise analytics.

```
                     OPERATIONAL BUSINESS PROCESSES
────────────────────────────────────────────────────────────────────────────

        Product Design & Merchandising
                    │
                    ▼
        Sourcing & Manufacturing
                    │
                    ▼
      Inventory & Warehouse Operations
                    │
                    ▼
      Omnichannel Sales & Commerce
                    │
                    ▼
      Customer Service & Returns
                    │
                    ▼
         Finance & Accounting
                    │
                    ▼

────────────────────────────────────────────────────────────────────────────

              ENTERPRISE ANALYTICS PLATFORM

                    │
                    ▼
          Python / Apache Airflow
                    │
                    ▼
     BigQuery Enterprise Data Warehouse
                    │
                    ▼
         dbt Transformation Models
                    │
                    ▼
     Enterprise Semantic Layer & KPIs
                    │
                    ▼
     Looker Studio Executive Dashboards
```

---

# Known Operational Constraints

The enterprise analytics platform is intentionally designed around several real-world operational limitations that influence data availability and reporting.

- Inventory synchronization between the Warehouse Management System and e-commerce platform occurs every four hours.
- Marketplace transaction data is received through scheduled API extractions and periodic CSV imports.
- Manufacturing quality logs are partially maintained by third-party suppliers, resulting in occasional data inconsistencies.
- Marketplace financial reconciliation is completed during the month-end close process rather than in real time.
- Customer return reason codes require standardization before they can be used for enterprise reporting.

These constraints intentionally simulate the challenges commonly encountered in rapidly growing organizations and demonstrate how the analytics platform resolves fragmented operational data through standardized engineering practices.

---

# Key Takeaways

The Enterprise Systems Landscape establishes the operational foundation of the Vespera Lifestyle Group analytics ecosystem. By documenting each source system, business owner, operational responsibility, and integration challenge, it provides a clear blueprint for designing scalable data pipelines, a governed enterprise data warehouse, and standardized executive reporting.

Together with the Business Capability Model and Core Business Processes, this document bridges business operations and technical architecture—demonstrating how operational data is transformed into trusted business intelligence through modern analytics engineering practices.