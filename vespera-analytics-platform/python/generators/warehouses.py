"""
Warehouse Master Generator

Generates the warehouse dimension from the enterprise configuration.

Unlike suppliers or customers, warehouses are fixed business assets,
so they are configuration-driven rather than randomly generated.
"""

from datetime import datetime
import pandas as pd

from config import WAREHOUSES


def generate_warehouses() -> pd.DataFrame:
    """
    Generate the warehouse master table.

    Returns
    -------
    pd.DataFrame
        Warehouse dimension.
    """

    warehouse_records = []

    for warehouse in WAREHOUSES:
        warehouse_records.append(
            {
                "warehouse_id": warehouse["warehouse_id"],
                "warehouse_name": warehouse["name"],
                "country": warehouse["country"],

                # Operational metadata
                "region": "Southeast Asia",
                "warehouse_type": "Distribution Center",

                # Lifecycle
                "opened_date": datetime(2022, 1, 1).date(),
                "active_flag": True,
            }
        )

    return pd.DataFrame(warehouse_records)