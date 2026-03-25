"""Bootstrap BigQuery tables for the Vitrine project."""
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
    ("products_raw", """
        product_id      INT64       NOT NULL,
        name            STRING      NOT NULL,
        brand           STRING,
        category        STRING      NOT NULL,
        department      STRING,
        retail_price    FLOAT64,
        cost            FLOAT64,
        created_at      TIMESTAMP,
        ingestion_date  DATE        NOT NULL
    """),
    ("products_clean", """
        product_id         INT64       NOT NULL,
        name               STRING      NOT NULL,
        brand              STRING      NOT NULL,
        category           STRING      NOT NULL,
        department         STRING      NOT NULL,
        retail_price       FLOAT64     NOT NULL,
        cost               FLOAT64     NOT NULL,
        margin_pct         FLOAT64,
        is_valid           BOOL        NOT NULL,
        validation_errors  STRING,
        cleaned_at         TIMESTAMP   NOT NULL,
        source_created_at  TIMESTAMP
    """),
    ("products_embedded", """
        product_id            INT64           NOT NULL,
        embedding_text        STRING          NOT NULL,
        embedding             ARRAY<FLOAT64>,
        embedding_model       STRING          NOT NULL,
        embedding_tokens      INT64           NOT NULL,
        embedding_cost_usd    FLOAT64,
        embedding_created_at  TIMESTAMP       NOT NULL
    """),
    ("products_clustered", """
        product_id              INT64     NOT NULL,
        cluster_id              INT64     NOT NULL,
        cluster_label           STRING,
        cluster_probability     FLOAT64,
        is_noise                BOOL      NOT NULL,
        clustering_algorithm    STRING    NOT NULL,
        min_cluster_size_param  INT64     NOT NULL,
        clustering_created_at   TIMESTAMP NOT NULL
    """),
    ("products_enriched", """
        product_id                INT64     NOT NULL,
        cluster_id                INT64,
        cluster_label             STRING,
        description_enriched      STRING    NOT NULL,
        description_model         STRING    NOT NULL,
        description_tone          STRING    NOT NULL,
        description_tokens_input  INT64,
        description_tokens_output INT64,
        description_cost_usd      FLOAT64,
        description_created_at    TIMESTAMP NOT NULL
    """),
    ("quality_report", """
        report_timestamp         TIMESTAMP NOT NULL,
        total_records            INT64     NOT NULL,
        valid_records            INT64     NOT NULL,
        completeness_pct         FLOAT64   NOT NULL,
        field_name_completeness  INT64,
        field_brand_completeness INT64,
        field_cat_completeness   INT64,
        field_price_completeness INT64,
        price_mean               FLOAT64,
        price_stddev             FLOAT64,
        price_min                FLOAT64,
        price_max                FLOAT64
    """),
    ("pipeline_runs", """
        run_id             STRING    NOT NULL,
        started_at         TIMESTAMP NOT NULL,
        completed_at       TIMESTAMP,
        status             STRING    NOT NULL,
        products_processed INT64,
        clusters_created   INT64,
        error_message      STRING
    """),
]

def main():
    client = get_client()

    for table_name, columns in TABLES:
        ddl = f"""
        CREATE TABLE IF NOT EXISTS
          `{PROJECT}.{DATASET}.{table_name}` ({columns})
        """
        print(f"  Creating {table_name}...", end=" ", flush=True)
        job = client.query(ddl)
        job.result()
        print("OK")

    print("\nAll tables created. Verifying:")
    for t in client.list_tables(f"{PROJECT}.{DATASET}"):
        print(f"  ✓ {t.table_id}")

if __name__ == "__main__":
    main()
