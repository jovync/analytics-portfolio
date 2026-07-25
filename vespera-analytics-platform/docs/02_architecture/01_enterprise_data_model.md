# Enterprise Data Model (Conceptual)

**Project:** Vespera Analytics Platform  
**Sprint:** 2 – Enterprise Architecture  
**Document Version:** 2.1  
**Status:** Approved

---

## 1. Purpose

The Enterprise Data Model (EDM) defines the high-level business entities, core concepts, and fundamental relationships across **Vespera Lifestyle Group**.

It establishes a unified business vocabulary for executive leadership, analytics engineering, and business intelligence. As a **conceptual model**, this document remains independent of physical databases, specific technology platforms, or underlying source application schemas.

This model serves as the architectural foundation for:

- Standardizing business definitions across disparate operational functions
- Establishing enterprise business entities and their conceptual relationships
- Guiding subsequent logical and dimensional schemas
- Aligning business strategy with analytical capabilities

---

## 2. Enterprise Data Modeling Philosophy

Vespera adopts a **canonical business model** that is later transformed into dimensional models optimized for enterprise analytics.

Operational business events across Vespera's value chain are first mapped into standardized, canonical enterprise business entities before being modeled into dimensional Star Schemas for analytical consumption. This approach decouples the conceptual business domain from the operational software stack, ensuring the analytics architecture remains resilient to software migrations, platform changes, and channel expansions.

---

## 3. Design Principles

### Business-First Modeling

Entities represent real-world commercial concepts rather than application-specific data structures or transactional database tables.

### Platform & Vendor Independence

Entities are defined purely by business function without referencing specific software tools, databases, or API protocols.

### Event-Driven Dynamics

Business facts originate from state-changing enterprise events—such as placing an order, completing a production batch, receiving stock, or issuing a refund.

### Conformed Shared Context

Core dimensions (such as Product, Customer, Store, and Calendar) are defined once at the enterprise level and shared across all analytical domains to prevent conflicting metrics.

---

## 4. Enterprise Business Entity Taxonomy

The taxonomy below illustrates how top-level enterprise concepts decompose into core business entities, events, and operational domains.

```text
Vespera Enterprise
├── Master Data Entities
│   ├── Customer
│   ├── Product
│   │   ├── SKU
│   │   ├── Category
│   │   └── Collection
│   ├── Supplier
│   ├── Store / Channel
│   ├── Warehouse / Facility
│   └── Employee
│
└── Commercial & Operational Events
    ├── Order
    ├── Return
    ├── Campaign
    ├── Production Batch
    ├── Inventory Movement
    └── Financial Ledger
```

---

## 5. Core Business Entities & Relationships

The following conceptual entities represent the primary business objects that participate in Vespera's enterprise value chain. Detailed attributes and business keys are intentionally deferred to the Logical Data Model.

### Customer

Represents an individual or organization interacting with Vespera across any commercial channel.

**Conceptual Relationships:**

- Places **Orders**
- Initiates **Returns**
- Engages with **Marketing Campaigns**
- Submits **Support Inquiries**

### Product

Represents sellable goods, merchandise styles, or physical items produced and commercialized by Vespera.

**Conceptual Relationships:**

- Categorized into **Product Categories** and **Collections**
- Manufactured via **Production Batches**
- Stored within **Warehouses**
- Sold via **Stores / Channels**
- Referenced in **Orders**

### Supplier

Represents external vendors, workshops, or material providers supplying finished goods or raw materials.

**Conceptual Relationships:**

- Fulfills **Purchase Orders**
- Supplies materials for **Production Batches**

### Warehouse

Represents physical distribution centers or fulfillment facilities storing company inventory.

**Conceptual Relationships:**

- Holds **Inventory Balances**
- Receives stock from **Production Batches**
- Dispatches items for **Orders**

### Store / Channel

Represents physical boutiques, online storefronts, or digital marketplaces where commercial transactions occur.

**Conceptual Relationships:**

- Generates **Orders**
- Processes **Returns**
- Maintains local **Inventory Balances**

### Production Batch

Represents a discrete manufacturing run of finished goods or components.

**Conceptual Relationships:**

- Executed by **Suppliers** / Internal Facilities
- Yields **Products**
- Deposits goods into **Warehouses**

### Order

Represents a commercial agreement between a Customer and Vespera to exchange goods for currency.

**Conceptual Relationships:**

- Placed by a **Customer**
- Generated through a **Store / Channel**
- Composed of **Products**
- Triggers **Financial Ledger** updates

---

## 6. High-Level Enterprise Data Flow

```text
Supplier
    │
    ▼
Production Batch
    │
    ▼
Product
    │
    ▼
Warehouse
    │
    ▼
Store / Channel
    │
    ▼
Customer
    │
    ▼
Order / Return
    │
    ▼
Financial Ledger
```

---

## 7. Business Domain Ownership

Data governance accountability is assigned to business functional roles to ensure entity definition consistency across the organization.

| Business Domain | Core Entities & Events | Executive Business Owner |
|-----------------|------------------------|--------------------------|
| **Enterprise Master Data** | Customer, Product Master, Calendar | Head of Data Governance |
| **Sales & Omnichannel** | Order, Store / Channel | VP of Retail & E-Commerce |
| **Supply Chain & Logistics** | Warehouse, Inventory Movement | VP of Supply Chain |
| **Manufacturing & Sourcing** | Supplier, Production Batch | Director of Manufacturing |
| **Marketing & Growth** | Campaign, Customer Engagement | Marketing Director |
| **Finance & Commercial** | Return, Financial Ledger | Head of Finance |

---

## 8. Architectural Scope

To maintain conceptual integrity, this document intentionally excludes:

- Physical database tables and schema names
- Primary keys, foreign keys, and surrogate keys
- Data types, field lengths, and nullability constraints
- Source system mappings and API specifications
- Column-level metadata definitions
- Pipeline orchestration and ETL implementation details

These artifacts are defined in subsequent architecture documents within Sprint 2.

---

## 9. Enterprise Architecture Roadmap

This conceptual document serves as the high-level foundation for the structured architectural sequence.

```text
[01_enterprise_data_model.md]      (Conceptual Model - YOU ARE HERE)
                 │
                 ▼
[02_logical_data_model.md]         (Logical Entities, Attributes & Cardinality)
                 │
                 ▼
[03_star_schema.md]                (Dimensional Modeling, Facts & Grain Strategy)
                 │
                 ▼
[04_physical_erd.md]               (Physical Warehouse Schema, Keys & Types)
                 │
                 ▼
[05_data_dictionary.md]            (Field Specifications, Nullability & Rules)
```