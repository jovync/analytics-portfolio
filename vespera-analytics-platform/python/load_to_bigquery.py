"""
load_to_bigquery.py

Loads all generated CSV files from data/raw/ into BigQuery,
creating the vespera_dw_raw dataset if it doesn't already exist.

This is a raw/batch load only — no transformation happens here.
Cleaning, typing, and business logic are handled downstream in
dbt staging models, consistent with an ELT (not ETL) pattern.

Run:

    python load_to_bigquery.py
"""

from pathlib import Path

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from config import RAW_DATA_DIR


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ID = "vespera-analytics-platform"

DATASET_ID = "vespera_dw_raw"

# Singapore, matching Vespera's HQ location. BigQuery free tier
# limits apply identically regardless of region.
DATASET_LOCATION = "asia-southeast1"

# Maps CSV filename (in data/raw/) -> target BigQuery table name.
# Table names follow a raw_ prefix convention so staging models can
# clearly distinguish "raw_orders" (this layer) from "stg_orders"
# (dbt staging layer) later.

TABLE_MAP = {

    "suppliers.csv": "raw_suppliers",
    "products.csv": "raw_products",
    "customers.csv": "raw_customers",
    "warehouses.csv": "raw_warehouses",
    "warehouse_product_assignment.csv": "raw_warehouse_product_assignment",
    "inventory_snapshot.csv": "raw_inventory_snapshot",
    "purchase_orders.csv": "raw_purchase_orders",
    "orders.csv": "raw_orders",
    "order_items.csv": "raw_order_items",
    "shipments.csv": "raw_shipments",
    "returns.csv": "raw_returns",
    "inventory_movements.csv": "raw_inventory_movements",
    "marketing_spend.csv": "raw_marketing_spend",

}


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def ensure_dataset_exists(client: bigquery.Client) -> None:
    """
    Creates the vespera_dw_raw dataset if it doesn't already exist.
    Safe to call on every run.
    """

    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"

    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_ref} already exists.")

    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = DATASET_LOCATION
        client.create_dataset(dataset)
        print(
            f"Created dataset {dataset_ref} in {DATASET_LOCATION}."
        )


def load_csv_to_table(
    client: bigquery.Client,
    csv_path: Path,
    table_name: str,
) -> int:
    """
    Loads a single CSV into a BigQuery table with schema
    auto-detection. WRITE_TRUNCATE means re-running this script is
    safe and idempotent — each run fully replaces the table rather
    than appending duplicate rows.

    Returns the number of rows loaded.
    """

    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    with open(csv_path, "rb") as csv_file:

        load_job = client.load_table_from_file(
            csv_file,
            table_ref,
            job_config=job_config,
        )

    load_job.result()  # blocks until the load completes

    table = client.get_table(table_ref)

    return table.num_rows


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    client = bigquery.Client(project=PROJECT_ID)

    print("=" * 60)
    print("Vespera Analytics Platform")
    print("BigQuery Raw Data Load")
    print("=" * 60)

    ensure_dataset_exists(client)

    print()

    results = []

    for filename, table_name in TABLE_MAP.items():

        csv_path = RAW_DATA_DIR / filename

        if not csv_path.exists():
            print(f"SKIPPED (file not found): {filename}")
            continue

        print(f"Loading {filename} -> {table_name} ...")

        row_count = load_csv_to_table(
            client=client,
            csv_path=csv_path,
            table_name=table_name,
        )

        results.append((table_name, row_count))

        print(f"  Loaded {row_count:,} rows.")

    print()
    print("=" * 60)
    print("Load Complete")
    print("=" * 60)

    for table_name, row_count in results:
        print(f"{table_name:<40} {row_count:>10,}")

    total_rows = sum(count for _, count in results)
    print(f"\nTotal rows loaded: {total_rows:,}")

    print(
        f"\nView your dataset at:\n"
        f"https://console.cloud.google.com/bigquery"
        f"?project={PROJECT_ID}&d={DATASET_ID}&p={PROJECT_ID}&page=dataset"
    )


if __name__ == "__main__":
    main()