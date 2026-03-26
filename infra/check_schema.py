"""Check the schema of thelook_ecommerce.products."""
import os
from google.oauth2 import service_account
from google.cloud import bigquery

KEY_FILE = os.path.expanduser("~/vitrine-sa-key.json")

creds = service_account.Credentials.from_service_account_file(
    KEY_FILE, scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
client = bigquery.Client(project="vitrine-wamba-2026", credentials=creds)

sql = """
SELECT column_name, data_type
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'products'
ORDER BY ordinal_position
"""
for row in client.query(sql).result():
    print(f"  {row.column_name}: {row.data_type}")
