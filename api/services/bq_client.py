"""Shared BigQuery client (singleton per process)."""
import os
from functools import lru_cache
from google.oauth2 import service_account
from google.cloud import bigquery

from config import PROJECT

KEY_FILE = os.environ.get(
    "GOOGLE_APPLICATION_CREDENTIALS",
    os.path.expanduser("~/vitrine-sa-key.json"),
)


@lru_cache(maxsize=1)
def get_bq_client() -> bigquery.Client:
    if os.path.exists(KEY_FILE):
        creds = service_account.Credentials.from_service_account_file(
            KEY_FILE,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(project=PROJECT, credentials=creds)
    return bigquery.Client(project=PROJECT)
