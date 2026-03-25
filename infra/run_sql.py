"""Run SQL pipeline steps against BigQuery using the service account key."""
import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from google.cloud import bigquery

PROJECT = "vitrine-wamba-2026"
DATASET = "vitrine_dataset"
KEY_FILE = os.path.expanduser("~/vitrine-sa-key.json")

SQL_DIR = Path(__file__).parent.parent / "sql"

STEPS = [
    ("01_staging.sql",  "products_raw from thelook_ecommerce.products"),
    ("02_transform.sql", "products_clean from products_raw"),
]


def get_client() -> bigquery.Client:
    creds = service_account.Credentials.from_service_account_file(
        KEY_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return bigquery.Client(project=PROJECT, credentials=creds)


def run_statement(client: bigquery.Client, sql: str, label: str) -> None:
    """Execute a single SQL statement and wait for completion."""
    job = client.query(sql)
    job.result()
    if job.errors:
        raise RuntimeError(f"BQ errors in {label}: {job.errors}")


def _strip_sql_comments(sql: str) -> str:
    """Remove single-line SQL comments to avoid splitting on semicolons inside them."""
    lines = []
    for line in sql.split("\n"):
        idx = line.find("--")
        lines.append(line[:idx] if idx != -1 else line)
    return "\n".join(lines)


def run_file(client: bigquery.Client, path: Path, description: str) -> None:
    """Execute only the first CREATE OR REPLACE TABLE statement from a SQL file."""
    raw = path.read_text(encoding="utf-8")

    # Strip comments first, then split on semicolons
    stripped = _strip_sql_comments(raw)
    statements = [s.strip() for s in stripped.split(";") if s.strip()]
    if not statements:
        raise ValueError(f"No statements found in {path.name}")

    first = statements[0]
    print(f"  [{path.name}] {description} ...", flush=True)
    run_statement(client, first, path.name)
    print(f"  [{path.name}] OK")


def verify(client: bigquery.Client) -> None:
    print("\nVerification:")
    for table in ["products_raw", "products_clean"]:
        sql = f"SELECT COUNT(*) AS n FROM `{PROJECT}.{DATASET}.{table}`"
        rows = list(client.query(sql).result())
        print(f"  {table}: {rows[0].n:,} rows")


def main() -> None:
    client = get_client()
    for filename, description in STEPS:
        run_file(client, SQL_DIR / filename, description)
    verify(client)
    print("\nAll steps complete.")


if __name__ == "__main__":
    main()
