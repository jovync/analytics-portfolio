# Enterprise Data Model

## Project Overview

The Enterprise Data Model (EDM) defines the foundational analytical architecture for **Vespera Lifestyle Group**, a fast-growing omnichannel lifestyle brand operating across Southeast Asia. As the company expanded across multiple countries, sales channels, and operational systems, reporting became increasingly fragmented, inventory visibility declined, and executive decision-making slowed due to inconsistent business metrics and disconnected data sources.

The purpose of this model is to establish a governed, enterprise-wide source of truth by integrating data across core business systems—including ERP, POS, e-commerce, warehouse management, manufacturing, CRM, and digital marketing platforms. By standardizing business definitions and consolidating operational data into a unified analytics platform, leadership can monitor business performance with confidence while reducing manual reporting effort and improving cross-functional alignment.

Designed using industry-standard dimensional modeling principles, the architecture supports scalable reporting, executive dashboards, operational analytics, and future advanced use cases such as demand forecasting, customer lifetime value (LTV) modeling, and predictive inventory optimization. More importantly, it creates a sustainable data foundation that enables Vespera Lifestyle Group to make faster, more informed business decisions as the organization continues to grow.

---

## Enterprise Business Capability Model

The Enterprise Business Capability Model organizes Vespera Lifestyle Group's operations into six core business domains. These domains represent the organization's end-to-end value chain and define the major operational areas supported by the analytics platform.

### 1. Master Data & Governance

Provides the enterprise-wide foundation for consistent and reliable reporting by maintaining standardized master data across products, customers, suppliers, stores, and organizational hierarchies. This domain resolves common data quality challenges such as duplicate supplier records, inconsistent product naming across channels, and conflicting business definitions, ensuring that all departments operate from a shared source of truth.

---

### 2. Omnichannel Sales & Commerce

Consolidates customer transactions across all commercial channels—including physical retail stores, e-commerce, regional marketplaces, and wholesale partners—into a unified sales domain. This capability enables consistent revenue reporting, channel performance analysis, and customer purchasing insights regardless of where a transaction originates, while providing standardized calculations for discounts, promotions, commissions, taxes, and net revenue.

---

### 3. Supply Chain, Inventory & Logistics

Supports end-to-end inventory visibility across suppliers, warehouses, distribution centers, and retail locations. This domain monitors inventory availability, stock movements, fulfillment performance, and logistics operations while enabling proactive management of stockouts, replenishment planning, and inventory allocation between physical and digital sales channels.

---

### 4. Sourcing & Manufacturing Operations

Provides visibility into the complete product production lifecycle, from raw material procurement through manufacturing, quality assurance, and finished goods receipt. By combining production performance with supplier and cost data, this domain enables operational leaders to evaluate manufacturing efficiency, product quality, supplier reliability, production costs, and overall supply performance.

---

### 5. Marketing & Customer Growth

Integrates digital marketing performance with customer purchasing behavior to provide a complete view of customer acquisition and retention. By connecting campaign investment with downstream sales, profitability, and repeat purchase behavior, this domain enables accurate measurement of customer acquisition cost (CAC), return on advertising spend (ROAS), customer lifetime value (LTV), and overall marketing effectiveness.

---

### 6. Customer Experience & Reverse Logistics

Captures customer service interactions, product returns, and post-purchase activities to measure customer satisfaction and operational quality. This domain enables analysis of return reasons, service performance, product defects, and reverse logistics costs while connecting customer feedback directly to manufacturing quality, merchandising decisions, and product improvements.

---

## Core Business Processes

An enterprise analytics platform is built around **business events**—not organizational departments or individual software applications. Every customer purchase, inventory movement, production run, financial transaction, and marketing interaction generates operational data that can be transformed into business intelligence.

The following section outlines the core business processes across **Vespera Lifestyle Group** and the operational events that generate the data powering its enterprise analytics platform.

---

### 1. Product Lifecycle & Master Catalog Setup

#### The Real-World Process

Before a product can be sold, it progresses from concept and design through product development, receives a unique Stock Keeping Unit (SKU), is assigned regional pricing and cost structures, and becomes available across the company's sales channels.

#### Data Generating Events

- **SKU Creation:** Merchandising creates master product records containing attributes such as category, collection, color, size, and season.
- **Bill of Materials (BOM) Definition:** Sourcing associates raw materials, packaging specifications, and estimated production costs with each product.
- **Pricing & Markdown Management:** Retail Operations establishes base retail prices, promotional pricing, and regional pricing strategies.

> **Business Value**
>
> This process establishes the trusted product foundation used throughout the analytics platform, enabling consistent reporting across sales performance, inventory valuation, manufacturing efficiency, merchandising effectiveness, and product profitability.

---

### 2. Sourcing, Manufacturing & Inbound Receiving

#### The Real-World Process

Vespera Lifestyle Group procures raw materials and finished goods from strategic suppliers, contract manufacturers, and internal production facilities. Products are manufactured, inspected for quality, and delivered to the Regional Distribution Center (RDC).

#### Data Generating Events

- **Purchase Order Creation:** Procurement records expected quantities, negotiated costs, suppliers, and delivery commitments.
- **Production Execution:** Manufacturing tracks production batches, raw material consumption, work-in-progress, and completion dates.
- **Quality Assurance Inspection:** Quality teams record inspection results, accepted quantities, rejected units, and standardized defect codes.
- **Goods Receipt:** Warehouse Operations validates inbound deliveries, records quantity variances, and updates inventory availability.

> **Business Value**
>
> These events establish the analytical foundation for procurement and vendor performance reporting, enabling supply chain leadership to monitor factory lead times, production efficiency, supplier quality, manufacturing costs, and vendor reliability.

---

### 3. Inventory Allocation & Movement

#### The Real-World Process

Inventory is stored within regional distribution centers before being allocated to physical retail stores or reserved for direct-to-consumer e-commerce fulfillment. Throughout its lifecycle, inventory continuously moves between warehouses, stores, and customers.

#### Data Generating Events

- **Inventory Allocation:** Supply Chain reserves stock for specific stores, regions, or fulfillment channels.
- **Warehouse Transfer & Dispatch:** Warehouse teams pick, pack, and ship inventory to retail locations or fulfillment operations.
- **Store Receiving:** Retail locations verify deliveries, record discrepancies, and update local inventory balances.
- **Inventory Counts & Adjustments:** Cycle counts and physical inventory audits record inventory variances, shrinkage, and stock corrections.

> **Business Value**
>
> Capturing these events provides enterprise-wide inventory visibility, quantifies the operational impact of synchronization delays between warehouse and e-commerce systems, and enables proactive monitoring of stock availability, replenishment, inventory accuracy, and shrinkage.

---

### 4. Omnichannel Sales & Order Fulfillment

#### The Real-World Process

Customers purchase products through physical retail stores, the company's e-commerce platform, regional marketplaces, and wholesale partners. Orders are processed, fulfilled, shipped, and ultimately settled through multiple payment channels.

#### Data Generating Events

- **Order Placement:** Sales systems record customer orders, purchased products, quantities, discounts, taxes, payment methods, and currencies.
- **Order Fulfillment:** Warehouse Operations picks, packs, and dispatches customer orders while generating shipping and fulfillment milestones.
- **Retail Register Reconciliation:** Physical stores perform end-of-day cash drawer balancing and payment reconciliation.
- **Marketplace Settlement:** Marketplace platforms release customer payments after deducting commissions, shipping subsidies, taxes, and promotional costs.

> **Business Value**
>
> Standardizing these events creates the enterprise sales dataset used to analyze channel performance, customer purchasing behavior, revenue trends, promotional effectiveness, and executive commercial performance across every market.

---

### 5. Returns, Exchanges & Reverse Logistics

#### The Real-World Process

Customers return products through retail stores or e-commerce channels due to quality issues, incorrect sizing, damaged products, or changes in purchasing decisions. Returned products are inspected before being restocked, refurbished, liquidated, or disposed.

#### Data Generating Events

- **Return Authorization:** Customers initiate returns while selecting standardized return reason codes.
- **Return Inspection:** Warehouse or retail staff evaluate product condition and assign inventory disposition statuses.
- **Refund Processing:** Finance processes refunds, payment reversals, exchanges, or store credit issuance.

> **Business Value**
>
> Linking return events back to original sales transactions, customer segments, marketing campaigns, and manufacturing batches enables leadership to identify quality issues, quantify margin erosion, reduce return rates, and improve customer satisfaction.

---

### 6. Customer Acquisition & Engagement

#### The Real-World Process

Potential customers discover the brand through digital marketing campaigns, visit the company's online channels, create customer accounts, enroll in loyalty programs, and interact with customer service throughout their purchasing journey.

#### Data Generating Events

- **Marketing Campaign Performance:** Advertising platforms record campaign spend, impressions, clicks, conversions, and engagement metrics.
- **Customer Registration:** Customers create profiles, provide contact preferences, and enroll in loyalty programs.
- **Customer Service Interaction:** Support teams record inquiries, complaints, service requests, and case resolution timelines.

> **Business Value**
>
> Integrating external marketing platforms with first-party customer data enables reliable attribution modeling, allowing the business to measure Customer Acquisition Cost (CAC), Customer Lifetime Value (LTV), campaign profitability, customer retention, and long-term customer value.

---

### 7. Financial Management & Performance

#### The Real-World Process

Financial transactions generated across procurement, manufacturing, inventory, sales, payroll, and marketplace operations are reconciled to produce accurate financial statements, profitability reporting, and executive performance metrics.

#### Data Generating Events

- **General Ledger Posting:** Finance records journal entries across operational and financial accounts.
- **Revenue Recognition:** Revenue is recognized according to established accounting policies following completed customer transactions.
- **Marketplace Reconciliation:** Marketplace settlements are reconciled against bank deposits after accounting for commissions, taxes, refunds, and shipping subsidies.
- **Cost Allocation:** Operational costs are allocated across products, channels, and business units while calculating Cost of Goods Sold (COGS).
- **Period-End Close:** Finance performs closing adjustments and finalizes monthly financial reporting.

> **Business Value**
>
> These events become the foundation for executive financial dashboards, automated financial reconciliation, profitability analysis, gross margin reporting, and accelerated month-end financial close processes.

---

### 8. Enterprise Analytics & Decision Support

#### The Real-World Process

Operational data generated across the organization is extracted, validated, standardized, and integrated into the enterprise analytics platform. Enterprise business rules are applied to produce trusted metrics that power executive dashboards, self-service reporting, advanced analytics, and strategic decision-making.

#### Data Generating Events

- **Pipeline Execution:** Automated orchestration processes extract and load incremental operational data into the enterprise data platform.
- **Data Quality Validation:** Automated validation rules detect duplicate records, missing values, schema inconsistencies, and business rule violations.
- **Business Metric Calculation:** Enterprise transformation models calculate standardized KPIs, including Net Revenue, Gross Margin, Inventory Turnover, Customer Lifetime Value (LTV), and Customer Acquisition Cost (CAC).
- **Analytical Model Refresh:** Curated dimensional models and presentation-layer datasets are refreshed for enterprise reporting.
- **Dashboard Publication:** Executive dashboards and self-service analytical reports are updated with the latest validated business data.

> **Business Value**
>
> This is where fragmented operational data becomes trusted business intelligence. By standardizing business definitions, automating reporting, and establishing a governed single source of truth, the analytics platform enables executives to monitor performance in near real time, identify operational issues earlier, and make confident, data-driven decisions as the organization continues to scale.

---

# Enterprise Systems Landscape

## Purpose

The Enterprise Systems Landscape documents the operational systems that generate data across **Vespera Lifestyle Group**. Each system supports one or more core business processes and acts as a **system of record** supplying operational data to the enterprise analytics platform.

By identifying system ownership, operational responsibilities, data generation types, synchronization frequencies, and integration challenges, this document establishes the foundation for enterprise data governance, ETL/ELT pipeline design, and executive reporting.

---

## Enterprise Analytics Architecture

```
                  +-----------------------------------+
                  |       Executive Dashboards        |
                  |          (Looker Studio)          |
                  +-----------------▲-----------------+
                                    │
                  +-----------------+-----------------+
                  |   Semantic Analytics Layer        |
                  |   Enterprise KPIs & Metrics       |
                  +-----------------▲-----------------+
                                    │
                  +-----------------+-----------------+
                  |     Enterprise Data Warehouse     |
                  |            (BigQuery)             |
                  +-----------------▲-----------------+
                                    │
                  +-----------------+-----------------+
                  |        Transformation Layer       |
                  |               (dbt)               |
                  +-----------------▲-----------------+
                                    │
                  +-----------------+-----------------+
                  |     ETL / Orchestration Engine    |
                  |      (Python / Apache Airflow)    |
                  +-----------------▲-----------------+
                                    │

──────────────────────────────────────────────────────────────────────────────

                      OPERATIONAL SOURCE SYSTEMS

 ERP / Finance      Omnichannel POS      E-Commerce      Warehouse Management
   NetSuite           Shopify POS        Shopify Plus        Logiwa WMS

 Manufacturing      CRM & Support      Marketing       Marketplace Platforms
 Custom MES           Zendesk       Meta / Google / TikTok   Shopee / Lazada
```

---

## Source Systems Inventory & Governance

The table below catalogs every operational system feeding into the Vespera Lifestyle Group enterprise analytics platform, mapping each system to its business owner, technology platform, synchronization frequency, and primary integration challenges.

| Core Business Process | Source System | Technology Platform | Business Owner | Data Generated | Update Frequency | Primary Data Quality & Integration Challenge |
|----------------------|---------------|---------------------|----------------|---------------|-----------------|---------------------------------------------|
| **Product Lifecycle** | ERP / Product Information Management | Oracle NetSuite | Merchandising Director | SKU master records, product hierarchy, BOM, regional pricing | Scheduled Batch (Daily) | Duplicate supplier records and inconsistent SKU naming across sales channels |
| **Sourcing & Manufacturing** | Manufacturing Execution System | Custom Manufacturing System | Production Manager | Work-in-Progress (WIP), production batches, quality inspections, defect codes | Event Driven | Semi-manual factory logging results in incomplete production and quality records |
| **Inventory Movement** | Warehouse Management System | Logiwa WMS | VP of Supply Chain | Inventory balances, warehouse locations, transfer orders, pick/pack events | Scheduled Batch (Every 4 Hours) | Inventory synchronization delay causes stock discrepancies between warehouse and e-commerce channels |
| **Retail Sales** | Point of Sale | Shopify POS | Retail Operations Manager | Store transactions, cashier sessions, payment methods, register reconciliation | Near Real-Time | End-of-day register reconciliation creates temporary reporting delays |
| **Online Sales** | E-Commerce Platform | Shopify Plus | E-Commerce Lead | Online orders, customer profiles, checkout events, discount codes | Event Driven | Order status updates (refunds, cancellations) may arrive asynchronously |
| **Marketplace Sales** | Marketplace Platforms | Shopee & Lazada APIs | Marketplace Specialist | Marketplace orders, commissions, vouchers, shipping subsidies | Weekly Batch | Manual CSV exports require extensive normalization and currency reconciliation |
| **Reverse Logistics** | Customer Support & POS | Zendesk & Shopify POS | Customer Experience Lead | Return requests, inspection outcomes, refunds, customer complaints | Scheduled Batch (Daily) | Return reason descriptions lack standardization across channels |
| **Customer Engagement** | Marketing Platforms & CRM | Meta Ads, Google Ads, TikTok Ads, Klaviyo | Marketing Director | Campaign spend, impressions, clicks, conversions, email engagement | Scheduled Batch (Daily) | Marketing performance is disconnected from ERP profitability and return data |
| **Financial Performance** | ERP & General Ledger | Oracle NetSuite | Head of Finance | Journal entries, revenue recognition, COGS, financial statements | Month-End Close | Marketplace settlements require extensive manual reconciliation before financial close |

---

## Enterprise Data Flow

Data flows sequentially from operational business processes into the enterprise analytics platform before being transformed into trusted business intelligence.

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
                    │
                    ▼

────────────────────────────────────────────────────────────────────────────

          EXECUTIVE DECISION MAKING

• Monitor enterprise performance
• Identify operational bottlenecks
• Optimize inventory allocation
• Improve manufacturing efficiency
• Measure marketing profitability
• Accelerate financial reporting
• Support strategic growth and expansion
```

---

## Key Takeaways

The Enterprise Systems Landscape establishes the operational foundation of the Vespera Lifestyle Group analytics ecosystem. By documenting each source system, its business ownership, data responsibilities, and integration challenges, this architecture provides a clear blueprint for designing scalable ETL pipelines, a governed enterprise data warehouse, and executive reporting.

Most importantly, it illustrates how operational data generated across the organization is transformed into standardized business metrics, enabling leadership to make timely, data-driven decisions from a trusted, enterprise-wide source of truth.