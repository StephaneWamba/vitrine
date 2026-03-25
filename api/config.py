"""API configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT = "vitrine-wamba-2026"
DATASET = "vitrine_dataset"

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-3-small"
GPT_MODEL = "gpt-4o-mini"

TABLE_CLEAN = f"{PROJECT}.{DATASET}.products_clean"
TABLE_EMBEDDED = f"{PROJECT}.{DATASET}.products_embedded"
TABLE_CLUSTERED = f"{PROJECT}.{DATASET}.products_clustered"
TABLE_ENRICHED = f"{PROJECT}.{DATASET}.products_enriched"
TABLE_QUALITY = f"{PROJECT}.{DATASET}.quality_report"
