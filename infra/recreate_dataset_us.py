"""Recreate vitrine_dataset in US region (thelook_ecommerce is US-only)."""
import os
from google.oauth2 import service_account
from google.cloud import bigquery

PROJECT = "vitrine-wamba-2026"
DATASET = "vitrine_dataset"
KEY_FILE = os.path.expanduser("~/vitrine-sa-key.json")

def get_client() -> bigquery.Client:
    creds = service_account.Credentials.from_service_account_file(
        KEY_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return bigquery.Client(project=PROJECT, credentials=creds)

TABLES = [
    ("products_raw", [
        bigquery.SchemaField("product_id",     "INT64",   mode="REQUIRED"),
        bigquery.SchemaField("name",           "STRING",  mode="REQUIRED"),
        bigquery.SchemaField("brand",          "STRING"),
        bigquery.SchemaField("category",       "STRING",  mode="REQUIRED"),
        bigquery.SchemaField("department",     "STRING"),
        bigquery.SchemaField("retail_price",   "FLOAT64"),
        bigquery.SchemaField("cost",           "FLOAT64"),
        bigquery.SchemaField("created_at",     "TIMESTAMP"),
        bigquery.SchemaField("ingestion_date", "DATE",    mode="REQUIRED"),
    ]),
    ("products_clean", [
        bigquery.SchemaField("product_id",        "INT64",     mode="REQUIRED"),
        bigquery.SchemaField("name",              "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("brand",             "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("category",          "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("department",        "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("retail_price",      "FLOAT64",   mode="REQUIRED"),
        bigquery.SchemaField("cost",              "FLOAT64",   mode="REQUIRED"),
        bigquery.SchemaField("margin_pct",        "FLOAT64"),
        bigquery.SchemaField("is_valid",          "BOOL",      mode="REQUIRED"),
        bigquery.SchemaField("validation_errors", "STRING"),
        bigquery.SchemaField("cleaned_at",        "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("source_created_at", "TIMESTAMP"),
    ]),
    ("products_embedded", [
        bigquery.SchemaField("product_id",           "INT64",     mode="REQUIRED"),
        bigquery.SchemaField("embedding_text",       "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("embedding",            "FLOAT64",   mode="REPEATED"),
        bigquery.SchemaField("embedding_model",      "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("embedding_tokens",     "INT64",     mode="REQUIRED"),
        bigquery.SchemaField("embedding_cost_usd",   "FLOAT64"),
        bigquery.SchemaField("embedding_created_at", "TIMESTAMP", mode="REQUIRED"),
    ]),
    ("products_clustered", [
        bigquery.SchemaField("product_id",             "INT64",     mode="REQUIRED"),
        bigquery.SchemaField("cluster_id",             "INT64",     mode="REQUIRED"),
        bigquery.SchemaField("cluster_label",          "STRING"),
        bigquery.SchemaField("cluster_probability",    "FLOAT64"),
        bigquery.SchemaField("is_noise",               "BOOL",      mode="REQUIRED"),
        bigquery.SchemaField("clustering_algorithm",   "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("min_cluster_size_param", "INT64",     mode="REQUIRED"),
        bigquery.SchemaField("clustering_created_at",  "TIMESTAMP", mode="REQUIRED"),
    ]),
    ("products_enriched", [
        bigquery.SchemaField("product_id",                "INT64",     mode="REQUIRED"),
        bigquery.SchemaField("cluster_id",                "INT64"),
        bigquery.SchemaField("cluster_label",             "STRING"),
        bigquery.SchemaField("description_enriched",      "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("description_model",         "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("description_tone",          "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("description_tokens_input",  "INT64"),
        bigquery.SchemaField("description_tokens_output", "INT64"),
        bigquery.SchemaField("description_cost_usd",      "FLOAT64"),
        bigquery.SchemaField("description_created_at",    "TIMESTAMP", mode="REQUIRED"),
    ]),
    ("quality_report", [
        bigquery.SchemaField("report_timestamp",         "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("total_records",            "INT64",     mode="REQUIRED"),
        bigquery.SchemaField("valid_records",            "INT64",     mode="REQUIRED"),
        bigquery.SchemaField("completeness_pct",         "FLOAT64",   mode="REQUIRED"),
        bigquery.SchemaField("field_name_completeness",  "INT64"),
        bigquery.SchemaField("field_brand_completeness", "INT64"),
        bigquery.SchemaField("field_cat_completeness",   "INT64"),
        bigquery.SchemaField("field_price_completeness", "INT64"),
        bigquery.SchemaField("price_mean",               "FLOAT64"),
        bigquery.SchemaField("price_stddev",             "FLOAT64"),
        bigquery.SchemaField("price_min",                "FLOAT64"),
        bigquery.SchemaField("price_max",                "FLOAT64"),
    ]),
    ("pipeline_runs", [
        bigquery.SchemaField("run_id",             "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("started_at",         "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("completed_at",       "TIMESTAMP"),
        bigquery.SchemaField("status",             "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("products_processed", "INT64"),
        bigquery.SchemaField("clusters_created",   "INT64"),
        bigquery.SchemaField("error_message",      "STRING"),
    ]),
]

def main():
    client = get_client()

    # Delete existing dataset
    print("Deleting existing dataset (EU)...")
    client.delete_dataset(
        f"{PROJECT}.{DATASET}",
        delete_contents=True,
        not_found_ok=True,
    )
    print("Deleted.")

    # Recreate in US
    print("Creating dataset in US region...")
    dataset = bigquery.Dataset(f"{PROJECT}.{DATASET}")
    dataset.location = "US"
    dataset.description = "Vitrine retail catalog intelligence — TheLook ecommerce pipeline"
    client.create_dataset(dataset)
    print("Dataset created in US.")

    # Create tables
    for table_name, schema in TABLES:
        ref = f"{PROJECT}.{DATASET}.{table_name}"
        table = bigquery.Table(ref, schema=schema)
        client.create_table(table, exists_ok=True)
        print(f"  Table {table_name}: OK")

    print("\nAll tables ready in US region.")

if __name__ == "__main__":
    main()
