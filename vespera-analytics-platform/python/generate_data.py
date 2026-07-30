"""
generate_data.py

Master orchestration script for the
Vespera Analytics Platform.

Generates the complete synthetic enterprise dataset.

Run:

    python generate_data.py
"""

import random

from config import RANDOM_SEED, RAW_DATA_DIR

from utils import assign_demand_tiers

from generators.suppliers import generate_suppliers
from generators.products import generate_products
from generators.customers import generate_customers
from generators.warehouses import generate_warehouses

from generators.assignment import generate_product_warehouse_assignment

from generators.inventory_snapshot import generate_inventory_snapshot
from generators.purchase_orders import generate_purchase_orders

from generators.orders import generate_orders
from generators.order_items import generate_order_items

from generators.shipments import generate_shipments
from generators.returns import generate_returns
from generators.inventory_movements import generate_inventory_movements
from generators.marketing_spend import generate_marketing_spend

from generators.acquisition_attribution import generate_acquisition_attribution
from generators.ar_invoices import generate_ar_invoices


# --------------------------------------------------
# Configuration
# --------------------------------------------------

DATA_FOLDER = RAW_DATA_DIR


# --------------------------------------------------
# Inventory Sanity Check
# --------------------------------------------------

def check_inventory_balances(
    inventory_snapshot_df,
    inventory_movements_df,
):
    """
    Reconstructs running on-hand balance per (warehouse, product)
    from the opening snapshot plus the full movement ledger, and
    flags any that ever go negative. Negative on-hand is physically
    impossible and signals that purchase order cadence/quantity, or
    warehouse-product assignment, needs another look for that SKU.

    Diagnostic only — doesn't modify or fail the run.
    """

    opening = (
        inventory_snapshot_df
        .groupby(["warehouse_id", "product_id"])["quantity_on_hand"]
        .sum()
    )

    movement_deltas = (
        inventory_movements_df
        .groupby(["warehouse_id", "product_id"])["quantity"]
        .sum()
    )

    combined = opening.add(movement_deltas, fill_value=0)

    negative = combined[combined < 0]

    if negative.empty:
        print("Inventory check: no negative on-hand balances found.")
    else:
        print(
            f"Inventory check: {len(negative)} warehouse/product "
            f"combinations end with negative on-hand balance."
        )
        print(negative.sort_values().head(10))


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    random.seed(RANDOM_SEED)

    DATA_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 60)
    print("Vespera Analytics Platform")
    print("Synthetic Enterprise Simulation Engine")
    print("=" * 60)

    # --------------------------------------------------
    # Master Data
    # --------------------------------------------------

    print("\nGenerating Suppliers...")
    suppliers_df = generate_suppliers()

    print("Generating Products...")
    products_df = generate_products(
        suppliers_df=suppliers_df,
    )

    print("Generating Customers...")
    customers_df = generate_customers()

    print("Generating Warehouses...")
    warehouses_df = generate_warehouses()

    print("Generating Marketing Spend...")
    marketing_spend_df = generate_marketing_spend()

    # --------------------------------------------------
    # Demand Tiers + Warehouse/Product Assignment
    # --------------------------------------------------
    # Computed once and shared across inventory_snapshot,
    # purchase_orders, and order_items, so all three agree on
    # which warehouse carries which product.

    print("Assigning demand tiers...")
    demand_tiers = assign_demand_tiers(products_df)

    print("Assigning warehouse-product stocking...")
    assignment_df = generate_product_warehouse_assignment(
        products_df=products_df,
        warehouses_df=warehouses_df,
        demand_tiers=demand_tiers,
    )

    # --------------------------------------------------
    # Inventory (opening position + supply-side replenishment)
    # --------------------------------------------------

    print("Generating Inventory Snapshot...")
    inventory_snapshot_df = generate_inventory_snapshot(
        products_df=products_df,
        warehouses_df=warehouses_df,
        assignment_df=assignment_df,
    )

    print("Generating Purchase Orders...")
    purchase_orders_df = generate_purchase_orders(
        products_df=products_df,
        suppliers_df=suppliers_df,
        warehouses_df=warehouses_df,
        assignment_df=assignment_df,
        demand_tiers=demand_tiers,
    )

    # --------------------------------------------------
    # Sales
    # --------------------------------------------------

    print("Generating Orders...")
    orders_df = generate_orders(
        customers_df=customers_df,
        warehouses_df=warehouses_df,
    )

    print("Generating Order Items...")
    order_items_df = generate_order_items(
        orders_df=orders_df,
        products_df=products_df,
        assignment_df=assignment_df,
        warehouses_df=warehouses_df,
    )

    # --------------------------------------------------
    # Logistics
    # --------------------------------------------------

    print("Generating Shipments...")
    shipments_df = generate_shipments(
        orders_df=orders_df,
        customers_df=customers_df,
        warehouses_df=warehouses_df,
    )

    print("Generating Returns...")
    returns_df = generate_returns(
        shipments_df=shipments_df,
        order_items_df=order_items_df,
        products_df=products_df,
    )

    # --------------------------------------------------
    # Customer Acquisition Attribution
    # --------------------------------------------------

    print("\nGenerating Customer Acquisition Attribution...")
    acquisition_attribution_df = generate_acquisition_attribution(
        customers_df=customers_df,
        marketing_spend_df=marketing_spend_df,
    )

    # --------------------------------------------------
    # AR Invoices
    # --------------------------------------------------

    print("Generating AR Invoices...")
    ar_invoices_df = generate_ar_invoices(
        orders_df=orders_df,
        order_items_df=order_items_df,
    )

    # --------------------------------------------------
    # Inventory Ledger
    # --------------------------------------------------

    print("Generating Inventory Movements...")
    inventory_movements_df = generate_inventory_movements(
        orders_df=orders_df,
        order_items_df=order_items_df,
        returns_df=returns_df,
        purchase_orders_df=purchase_orders_df,
    )

    # --------------------------------------------------
    # Diagnostics
    # --------------------------------------------------

    print("\nRunning inventory balance check...")
    check_inventory_balances(
        inventory_snapshot_df=inventory_snapshot_df,
        inventory_movements_df=inventory_movements_df,
    )

    # --------------------------------------------------
    # Save Files
    # --------------------------------------------------

    print("\nSaving CSV files...")

    suppliers_df.to_csv(
        DATA_FOLDER / "suppliers.csv",
        index=False,
    )

    products_df.to_csv(
        DATA_FOLDER / "products.csv",
        index=False,
    )

    customers_df.to_csv(
        DATA_FOLDER / "customers.csv",
        index=False,
    )

    warehouses_df.to_csv(
        DATA_FOLDER / "warehouses.csv",
        index=False,
    )

    assignment_df.to_csv(
        DATA_FOLDER / "warehouse_product_assignment.csv",
        index=False,
    )

    inventory_snapshot_df.to_csv(
        DATA_FOLDER / "inventory_snapshot.csv",
        index=False,
    )

    purchase_orders_df.to_csv(
        DATA_FOLDER / "purchase_orders.csv",
        index=False,
    )

    orders_df.to_csv(
        DATA_FOLDER / "orders.csv",
        index=False,
    )

    order_items_df.to_csv(
        DATA_FOLDER / "order_items.csv",
        index=False,
    )

    shipments_df.to_csv(
        DATA_FOLDER / "shipments.csv",
        index=False,
    )

    returns_df.to_csv(
        DATA_FOLDER / "returns.csv",
        index=False,
    )

    inventory_movements_df.to_csv(
        DATA_FOLDER / "inventory_movements.csv",
        index=False,
    )

    marketing_spend_df.to_csv(
    DATA_FOLDER / "marketing_spend.csv",
    index=False,
    )

    acquisition_attribution_df.to_csv(
        DATA_FOLDER / "acquisition_attribution.csv",
        index=False,
    )

    ar_invoices_df.to_csv(
        DATA_FOLDER / "ar_invoices.csv",
        index=False,
    )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("Synthetic Enterprise Generation Complete")
    print("=" * 60)

    print(f"Suppliers:                    {len(suppliers_df):>10,}")
    print(f"Products:                     {len(products_df):>10,}")
    print(f"Customers:                    {len(customers_df):>10,}")
    print(f"Warehouses:                   {len(warehouses_df):>10,}")
    print(f"Warehouse-Product Assignment: {len(assignment_df):>10,}")
    print(f"Inventory Snapshot:           {len(inventory_snapshot_df):>10,}")
    print(f"Purchase Orders:              {len(purchase_orders_df):>10,}")
    print(f"Orders:                       {len(orders_df):>10,}")
    print(f"Order Items:                  {len(order_items_df):>10,}")
    print(f"Shipments:                    {len(shipments_df):>10,}")
    print(f"Returns:                      {len(returns_df):>10,}")
    print(f"Inventory Movements:          {len(inventory_movements_df):>10,}")
    print(f"Marketing Spend:              {len(marketing_spend_df):>10,}")
    print(f"Acquisition Attribution:      {len(acquisition_attribution_df):>10,}")
    print(f"AR Invoices:                  {len(ar_invoices_df):>10,}")

    print("\nCSV files saved to:")
    print(DATA_FOLDER.resolve())


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":
    main()