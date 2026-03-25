"""BigQuery client factory — uses service account key or ADC."""
import os
from google.oauth2 import service_account
from google.cloud import bigquery
from config import PROJECT, KEY_FILE


def get_client() -> bigquery.Client:
    if os.path.exists(KEY_FILE):
        creds = service_account.Credentials.from_service_account_file(
            KEY_FILE,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(project=PROJECT, credentials=creds)
    # Fallback to ADC (used inside Cloud Run)
    return bigquery.Client(project=PROJECT)
