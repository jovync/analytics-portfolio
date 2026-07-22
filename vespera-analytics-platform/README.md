# Vespera Analytics Platform

> An end-to-end enterprise analytics platform built for a fictional omnichannel retail company to demonstrate modern analytics engineering, data warehousing, and business intelligence skills.

---

## Overview

Vespera Lifestyle Group is a fictional fast-growing lifestyle retailer operating across Southeast Asia with multiple sales channels, warehouses, and regional business units.

As the company expanded, reporting became fragmented across ERP, POS, e-commerce, warehouse, finance, and marketing systems. Executive teams struggled with inconsistent KPIs, delayed reporting, inventory visibility issues, and manual reconciliation.

This project simulates a real enterprise analytics consulting engagement, where a modern data platform is designed to consolidate operational data into a governed, scalable analytics environment.

The objective is to build a complete analytics solution—from raw operational data to executive dashboards—using industry-standard data engineering and dimensional modeling practices.

---

# Business Problems

The platform addresses several enterprise challenges:

- Multiple departments reporting different revenue figures
- Manual reconciliation across ERP and marketplace data
- Inventory visibility issues caused by system synchronization delays
- Inconsistent product and supplier master data
- Marketing performance disconnected from profitability
- Slow executive reporting and decision-making

---

# Project Objectives

The project demonstrates how to:

- Design an Enterprise Data Warehouse using Kimball dimensional modeling
- Build scalable Star Schema data models
- Develop SQL transformations and analytics-ready datasets
- Create dbt transformation pipelines
- Implement data quality validation and governance
- Build executive dashboards for business stakeholders
- Simulate real-world enterprise analytics architecture

---

# Technology Stack

| Area | Technology |
|------|------------|
| Data Warehouse | BigQuery |
| SQL | BigQuery SQL |
| Data Transformation | dbt |
| Data Processing | Python |
| Pipeline Orchestration | Apache Airflow |
| BI & Visualization | Looker Studio |
| Version Control | Git & GitHub |

---

# Project Structure

```
docs/
│
├── 01_business/
├── 02_architecture/
├── 03_engineering/
└── 04_dashboards/

sql/
dbt/
python/
data/
dashboards/
```

---

# Documentation

## 01 Business

- Project Overview
- Business Capability Model
- Core Business Processes
- Enterprise Systems Landscape
- Enterprise KPI Framework

## 02 Architecture

- Enterprise Data Model
- Star Schema
- Entity Relationship Diagram (ERD)
- Data Dictionary

## 03 Engineering

- ETL Design
- dbt Transformation Specification
- Data Quality Framework

## 04 Dashboards

- Executive Dashboard
- Supply Chain Dashboard
- Finance Dashboard
- Marketing Dashboard

---

# Project Roadmap

- [x] Business Design
- [ ] Enterprise Data Model
- [ ] Data Warehouse
- [ ] SQL Development
- [ ] dbt Models
- [ ] Python Pipelines
- [ ] Data Quality Framework
- [ ] Dashboard Development
- [ ] Executive Case Study

---

## Portfolio Goal

This project is designed to showcase enterprise-level skills expected of Senior Data Analysts, Analytics Engineers, and Data Consultants by simulating the complete lifecycle of an enterprise analytics implementation—from business discovery and dimensional modeling through engineering and executive reporting.