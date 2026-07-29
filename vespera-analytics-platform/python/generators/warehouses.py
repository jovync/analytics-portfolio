"""
Warehouse Master Generator

Creates the enterprise fulfillment location master used by
the Vespera Analytics Platform.

The warehouse master is referenced by Inventory,
Order Fulfillment, Shipments, Returns,
and Inventory Movements.
"""

from __future__ import annotations

import pandas as pd

from config import WAREHOUSES


# =============================================================================
# GENERATOR
# =============================================================================

def generate_warehouses() -> pd.DataFrame:
    """
    Generate enterprise warehouse master.

    Returns
    -------
    pandas.DataFrame
    """

    warehouses_df = (
        pd.DataFrame(WAREHOUSES)
        .sort_values("warehouse_code")
        .reset_index(drop=True)
    )

    return warehouses_df


# =============================================================================
# Example
# =============================================================================

if __name__ == "__main__":

    warehouses_df = generate_warehouses()

    print(warehouses_df)
    print()
    print(warehouses_df.info())