"""
Vespera Enterprise Simulation Engine (VESE)
Global Configuration

Centralized configuration for the entire synthetic
enterprise simulation.

Every generator should import its defaults from this
module rather than hardcoding values.
"""

from pathlib import Path
from datetime import datetime

# =============================================================================
# PROJECT PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

RAW_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# =============================================================================
# RANDOMNESS
# =============================================================================

RANDOM_SEED = 42

# =============================================================================
# SIMULATION PERIOD
# =============================================================================

SIMULATION_START_DATE = datetime(2024, 1, 1)

SIMULATION_END_DATE = datetime(2025, 12, 31)

# =============================================================================
# ENTERPRISE DATA VOLUMES
# =============================================================================

NUM_SUPPLIERS = 30

NUM_CUSTOMERS = 10_000

NUM_PRODUCTS = 1_200

TARGET_ORDER_COUNT = 50_000

TARGET_RETURN_COUNT = 4_000

# =============================================================================
# BRANDS
# =============================================================================

BRANDS = [

    "Vespera Essentials",

    "Aura Home",

    "Lumina Living",

    "Solstice Active",

    "Zenith Gear",

    "Atelier V",

    "Halo Beauty",

    "Nord House",

]

# =============================================================================
# PRODUCT CATALOG
# =============================================================================

PRODUCT_CATALOG = {

    "Personal Care": {

        "return_rate": 0.03,

        "markup": (2.4, 3.2),

        "base_cost": (6, 30),

        "adjectives": [
            "Hydra Glow",
            "Daily Protect",
            "Botanical",
            "Radiant",
            "Pure",
            "Essential",
        ],

        "products": [
            "Serum",
            "Facial Cleanser",
            "Body Lotion",
            "Hand Wash",
            "Sunscreen",
            "Night Cream",
        ],

        "variants": [
            "30ml",
            "50ml",
            "100ml",
            "150ml",
            "200ml",
        ],
    },

    "Apparel": {

        "return_rate": 0.12,

        "markup": (2.1, 2.9),

        "base_cost": (12, 45),

        "adjectives": [
            "Classic",
            "Relaxed",
            "Essential",
            "Premium",
            "Tailored",
            "Urban",
        ],

        "products": [
            "Cotton Tee",
            "Linen Shirt",
            "Denim Jacket",
            "Knit Sweater",
            "Active Shorts",
            "Cargo Pants",
        ],

        "variants": [
            "XS",
            "S",
            "M",
            "L",
            "XL",
            "XXL",
        ],
    },

    "Accessories": {

        "return_rate": 0.04,

        "markup": (2.6, 3.4),

        "base_cost": (8, 40),

        "adjectives": [
            "Urban",
            "Daily",
            "Minimal",
            "Signature",
            "Travel",
            "Classic",
        ],

        "products": [
            "Backpack",
            "Wallet",
            "Card Holder",
            "Duffel Bag",
            "Water Bottle",
            "Cap",
        ],

        "variants": [
            "Black",
            "Navy",
            "Tan",
            "Grey",
            "Olive",
        ],
    },

    "Home & Living": {

        "return_rate": 0.05,

        "markup": (1.8, 2.6),

        "base_cost": (10, 90),

        "adjectives": [
            "Minimalist",
            "Nordic",
            "Classic",
            "Modern",
            "Elegant",
            "Organic",
        ],

        "products": [
            "Ceramic Mug",
            "Desk Lamp",
            "Throw Blanket",
            "Serving Board",
            "Storage Basket",
            "Diffuser",
        ],

        "variants": [
            "Small",
            "Medium",
            "Large",
            "Set of 2",
            "Set of 4",
        ],
    },

}

# =============================================================================
# WAREHOUSES
# =============================================================================
# serves_countries determines which customer countries a warehouse is
# eligible to fulfill orders for. Retail Stores only serve their own
# country (walk-in / local delivery). Distribution Centers serve a
# regional cluster, since they exist specifically to cover countries
# without their own physical store (e.g. no Malaysia or Singapore
# retail store exists, so the DCs in those countries pick up local
# + regional online fulfillment).
# =============================================================================

WAREHOUSES = [

    # ----------------------------------------------------------
    # Distribution Centers
    # ----------------------------------------------------------

    {
        "warehouse_id": "WH001",
        "warehouse_code": "SG_DC",
        "warehouse_name": "Singapore Distribution Center",
        "warehouse_type": "Distribution Center",
        "country": "Singapore",
        "city": "Singapore",
        "region": "Singapore",
        "serves_countries": ["Singapore", "Malaysia"],
    },

    {
        "warehouse_id": "WH002",
        "warehouse_code": "MY_DC",
        "warehouse_name": "Kuala Lumpur Distribution Center",
        "warehouse_type": "Distribution Center",
        "country": "Malaysia",
        "city": "Kuala Lumpur",
        "region": "Malaysia",
        "serves_countries": ["Malaysia", "Thailand", "Vietnam"],
    },

    # ----------------------------------------------------------
    # Retail Stores / Fulfillment Stores
    # ----------------------------------------------------------

    {
        "warehouse_id": "WH003",
        "warehouse_code": "PH_MNL",
        "warehouse_name": "Manila Flagship Store",
        "warehouse_type": "Retail Store",
        "country": "Philippines",
        "city": "Manila",
        "region": "Philippines",
        "serves_countries": ["Philippines"],
    },

    {
        "warehouse_id": "WH004",
        "warehouse_code": "PH_CEB",
        "warehouse_name": "Cebu Store",
        "warehouse_type": "Retail Store",
        "country": "Philippines",
        "city": "Cebu",
        "region": "Philippines",
        "serves_countries": ["Philippines"],
    },

    {
        "warehouse_id": "WH005",
        "warehouse_code": "TH_BKK",
        "warehouse_name": "Bangkok Store",
        "warehouse_type": "Retail Store",
        "country": "Thailand",
        "city": "Bangkok",
        "region": "Thailand",
        "serves_countries": ["Thailand"],
    },

    {
        "warehouse_id": "WH006",
        "warehouse_code": "VN_HCM",
        "warehouse_name": "Ho Chi Minh Store",
        "warehouse_type": "Retail Store",
        "country": "Vietnam",
        "city": "Ho Chi Minh City",
        "region": "Vietnam",
        "serves_countries": ["Vietnam"],
    },

    # ----------------------------------------------------------
    # Returns Center
    # ----------------------------------------------------------

    {
        "warehouse_id": "WH007",
        "warehouse_code": "SG_RTN",
        "warehouse_name": "Singapore Returns Center",
        "warehouse_type": "Returns Center",
        "country": "Singapore",
        "city": "Singapore",
        "region": "Singapore",
        "serves_countries": ["Singapore", "Malaysia", "Thailand", "Philippines", "Vietnam"],
    },

]

# =============================================================================
# CUSTOMER MARKETS
# =============================================================================

CUSTOMER_COUNTRIES = {

    "Singapore": 0.15,

    "Malaysia": 0.20,

    "Thailand": 0.20,

    "Philippines": 0.25,

    "Vietnam": 0.20,

}

# =============================================================================
# FAKER LOCALES
# =============================================================================

FAKER_LOCALES = {

    "Singapore": "en_US",       # Faker has no dedicated en_SG; closest general English locale
    "Malaysia": "en_US",        # ms_MY is not a valid/available Faker locale
    "Thailand": "th_TH",
    "Philippines": "en_PH",
    "Vietnam": "vi_VN",

}

# =============================================================================
# SALES CHANNELS
# =============================================================================

CHANNELS = {

    "Shopify": 0.40,

    "Shopee": 0.25,

    "Lazada": 0.20,

    "Retail": 0.15,

}

# =============================================================================
# ORDER STATUS
# =============================================================================

ORDER_STATUS = {

    "Pending": 0.05,

    "Processing": 0.10,

    "Shipped": 0.25,

    "Delivered": 0.55,

    "Cancelled": 0.05,

}

# =============================================================================
# PAYMENT METHODS
# =============================================================================

PAYMENT_METHODS = {

    "Credit Card": 0.40,

    "Digital Wallet": 0.30,

    "Bank Transfer": 0.15,

    "Cash on Delivery": 0.15,

}

# =============================================================================
# SHIPMENT STATUS
# =============================================================================

SHIPMENT_STATUS = {

    "Pending": 0.05,

    "In Transit": 0.20,

    "Delivered": 0.70,

    "Failed Delivery": 0.05,

}

# =============================================================================
# RETURN REASONS
# =============================================================================

RETURN_REASONS = {

    "Sizing Issue": 0.45,

    "Damaged": 0.20,

    "Not as Expected": 0.15,

    "Customer Remorse": 0.12,

    "Wrong Item": 0.08,

}

# =============================================================================
# INVENTORY MOVEMENT TYPES
# =============================================================================

INVENTORY_MOVEMENT_TYPES = {

    "Inbound Purchase": 0.25,

    "Customer Sale": 0.45,

    "Customer Return": 0.08,

    "Stock Transfer": 0.12,

    "Inventory Adjustment": 0.05,

    "Damaged Inventory": 0.05,

}

# =============================================================================
# SEASONALITY
# =============================================================================
# Monthly demand multipliers applied when sampling order_date, so
# order volume isn't flat across the simulation window. Weighted
# toward regional shopping events relevant to SEA e-commerce
# (9.9/10.10/11.11/12.12 flash sales, year-end holidays).
# These are relative weights, not probabilities — they get
# normalized wherever they're consumed.
# =============================================================================

SEASONALITY_MULTIPLIERS = {

    1: 0.90,   # Jan  - post-holiday lull
    2: 0.85,   # Feb  - slowest month
    3: 0.90,   # Mar
    4: 0.90,   # Apr
    5: 0.95,   # May
    6: 0.95,   # Jun
    7: 0.90,   # Jul
    8: 0.90,   # Aug
    9: 1.05,   # Sep  - 9.9 sale
    10: 1.10,  # Oct  - 10.10 sale
    11: 1.35,  # Nov  - 11.11, biggest SEA shopping event
    12: 1.40,  # Dec  - 12.12 + year-end holidays

}

# =============================================================================
# CUSTOMER ORDER FREQUENCY
# =============================================================================
# Relative likelihood a customer generates an order, by loyalty tier.
# Higher-tier customers order more often — this is what creates
# realistic repeat-purchase concentration (a small share of customers
# driving a disproportionate share of order volume) rather than every
# customer ordering with equal probability.
# =============================================================================

LOYALTY_ORDER_FREQUENCY_WEIGHTS = {

    "Bronze": 1.0,

    "Silver": 1.6,

    "Gold": 2.4,

    "Platinum": 3.5,

}

# =============================================================================
# MARKETING CHANNELS
# =============================================================================
# Only paid channels get ad spend. Organic Search and Referral are
# intentionally excluded — they're unpaid/indirect acquisition paths,
# so customers.py's ACQUISITION_CHANNELS assigns customers to them,
# but marketing_spend.py generates no spend rows for them. This is
# what makes CAC math meaningful: organic/referral customers count
# in the "new customers" denominator without inflating the spend
# numerator.
# =============================================================================

MARKETING_CHANNELS = {

    "Facebook Ads": {
        "platform": "Meta",
        "daily_budget_range": (150, 500),
    },

    "Instagram": {
        "platform": "Meta",
        "daily_budget_range": (120, 450),
    },

    "TikTok": {
        "platform": "TikTok",
        "daily_budget_range": (100, 400),
    },

    "Email Campaign": {
        "platform": "Klaviyo",
        "daily_budget_range": (20, 80),
    },

}

# =============================================================================
# TAX RATES
# =============================================================================
# Applied based on the fulfilling warehouse's country (point-of-sale
# jurisdiction), not the customer's country. Simplified to a single
# rate per country — real GST/VAT systems have category-specific
# exemptions and thresholds not modeled here.
# =============================================================================

TAX_RATES_BY_COUNTRY = {

    "Singapore": 0.09,    # GST
    "Malaysia": 0.06,     # SST
    "Thailand": 0.07,     # VAT
    "Philippines": 0.12,  # VAT
    "Vietnam": 0.10,      # VAT

}

# =============================================================================
# MARKETPLACE COMMISSION RATES
# =============================================================================
# Shopee/Lazada charge a seller commission on each sale; Shopify
# (own storefront) and Retail (in-store) do not.
# =============================================================================

MARKETPLACE_COMMISSION_RATES = {

    "Shopify": 0.00,
    "Shopee": 0.06,
    "Lazada": 0.05,
    "Retail": 0.00,

}

# =============================================================================
# RESTOCKING FEES
# =============================================================================
# Only charged when the return is the customer's choice (remorse),
# not when Vespera is at fault (damaged, wrong item shipped, sizing
# issue, not as expected).
# =============================================================================

RESTOCKING_FEE_APPLICABLE_REASONS = {"Customer Remorse"}

RESTOCKING_FEE_RATE = 0.10

# =============================================================================
# CONFIG ADDITIONS — append these blocks to config.py
# Added to support fact_ar_aging_daily and fact_marketing_spend
# (KPI Framework <-> Star Schema reconciliation, v1.2)
# =============================================================================

# -----------------------------------------------------------------------
# AR INVOICES
# -----------------------------------------------------------------------
# Simplification note: Vespera's customer base is modeled as pure B2C
# (no wholesale/B2B segment exists). Per project decision, invoices are
# generated against existing retail customers as a simplification rather
# than modeling a separate wholesale account type. See
# docs/06_kpi_schema_reconciliation.md, Section 5.
# -----------------------------------------------------------------------

# Share of orders that are invoiced on credit terms rather than settled
# immediately at point of sale. Kept deliberately small since this is a
# predominantly D2C/e-commerce business — DSO is a minority-case metric
# here, not the primary cash-flow story.
PCT_ORDERS_ON_CREDIT_TERMS = 0.07

PAYMENT_TERMS_WEIGHTS = {

    "NET15": 0.45,

    "NET30": 0.40,

    "NET60": 0.15,

}

PAYMENT_TERMS_DAYS = {

    "NET15": 15,

    "NET30": 30,

    "NET60": 60,

}

# Outcome distribution for invoiced orders. "Still Open" is only sampled
# for invoices whose due_date falls late enough in the simulation window
# that an unpaid balance is plausible (see _is_recent_enough_to_be_open
# in ar_invoices.py).
INVOICE_OUTCOME_WEIGHTS = {

    "Paid On Time": 0.65,

    "Paid Late": 0.22,

    "Partially Paid": 0.06,

    "Still Open": 0.07,

}

# -----------------------------------------------------------------------
# MARKETING CAMPAIGNS & SPEND
# -----------------------------------------------------------------------
# No additions needed here — marketing_spend.py already exists in the
# repo with its own MARKETING_CHANNELS config and campaign generation
# logic. acquisition_attribution.py consumes its output directly rather
# than requiring new config.
# -----------------------------------------------------------------------