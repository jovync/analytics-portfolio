"""
Vespera Enterprise Simulation Engine (VESE)
Global Configuration

This module centralizes all enterprise configuration values used by
the synthetic data simulation engine.
"""

from pathlib import Path
from datetime import datetime

# =============================================================================
# PROJECT PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

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
# DATA VOLUMES
# =============================================================================

NUM_SUPPLIERS = 30
NUM_CUSTOMERS = 10000
NUM_PRODUCTS = 1200

TARGET_ORDER_COUNT = 50000
TARGET_RETURN_COUNT = 4000

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
    "Nord House"
]

# =============================================================================
# PRODUCT CATALOG
# =============================================================================

PRODUCT_CATALOG = {

    "Personal Care": {

        "return_rate": 0.03,
        "markup": 2.8,
        "base_cost": (6, 30),

        "adjectives": [
            "Hydra Glow",
            "Daily Protect",
            "Botanical",
            "Radiant",
            "Pure",
            "Essential"
        ],

        "products": [
            "Serum 50ml",
            "Facial Cleanser",
            "Body Lotion",
            "Hand Wash",
            "Sunscreen SPF50",
            "Night Cream"
        ]
    },

    "Apparel": {

        "return_rate": 0.12,
        "markup": 2.5,
        "base_cost": (12, 45),

        "adjectives": [
            "Classic",
            "Relaxed",
            "Essential",
            "Premium",
            "Tailored",
            "Urban"
        ],

        "products": [
            "Cotton Tee",
            "Linen Shirt",
            "Denim Jacket",
            "Knit Sweater",
            "Active Shorts",
            "Cargo Pants"
        ]
    },

    "Accessories": {

        "return_rate": 0.04,
        "markup": 3.0,
        "base_cost": (8, 40),

        "adjectives": [
            "Urban",
            "Daily",
            "Minimal",
            "Signature",
            "Travel",
            "Classic"
        ],

        "products": [
            "Backpack",
            "Wallet",
            "Card Holder",
            "Duffel Bag",
            "Water Bottle",
            "Cap"
        ]
    },

    "Home & Living": {

        "return_rate": 0.05,
        "markup": 2.2,
        "base_cost": (10, 90),

        "adjectives": [
            "Minimalist",
            "Nordic",
            "Classic",
            "Modern",
            "Elegant",
            "Organic"
        ],

        "products": [
            "Ceramic Mug",
            "Desk Lamp",
            "Throw Blanket",
            "Serving Board",
            "Storage Basket",
            "Diffuser"
        ]
    }
}

# =============================================================================
# WAREHOUSES
# =============================================================================

WAREHOUSES = [

    {
        "warehouse_code": "SG_DC",
        "warehouse_name": "Singapore Distribution Center",
        "country": "Singapore"
    },

    {
        "warehouse_code": "PH_DC",
        "warehouse_name": "Manila Distribution Center",
        "country": "Philippines"
    },

    {
        "warehouse_code": "MY_DC",
        "warehouse_name": "Kuala Lumpur Distribution Center",
        "country": "Malaysia"
    },

    {
        "warehouse_code": "TH_DC",
        "warehouse_name": "Bangkok Distribution Center",
        "country": "Thailand"
    }

]

# =============================================================================
# SALES CHANNELS
# =============================================================================

CHANNELS = {

    "Shopify": 0.40,
    "Shopee": 0.25,
    "Lazada": 0.20,
    "Retail": 0.15

}

# =============================================================================
# RETURN REASONS
# =============================================================================

RETURN_REASONS = {

    "Sizing Issue": 0.45,
    "Damaged": 0.20,
    "Not as Expected": 0.15,
    "Customer Remorse": 0.12,
    "Wrong Item": 0.08

}