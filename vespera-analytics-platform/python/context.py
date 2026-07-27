"""
Enterprise Simulation Context

Acts as shared memory between all simulation modules.
"""

from dataclasses import dataclass, field
import pandas as pd


@dataclass
class EnterpriseContext:

    suppliers: pd.DataFrame = field(default_factory=pd.DataFrame)

    customers: pd.DataFrame = field(default_factory=pd.DataFrame)

    warehouses: pd.DataFrame = field(default_factory=pd.DataFrame)

    products: pd.DataFrame = field(default_factory=pd.DataFrame)

    orders: pd.DataFrame = field(default_factory=pd.DataFrame)

    order_lines: pd.DataFrame = field(default_factory=pd.DataFrame)

    purchase_orders: pd.DataFrame = field(default_factory=pd.DataFrame)

    inventory: pd.DataFrame = field(default_factory=pd.DataFrame)

    returns: pd.DataFrame = field(default_factory=pd.DataFrame)