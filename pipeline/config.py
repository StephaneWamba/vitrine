"""Pipeline configuration — all constants in one place."""
import os

# ── GCP ───────────────────────────────────────────────────────────────────
PROJECT = "vitrine-wamba-2026"
DATASET = "vitrine_dataset"
KEY_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS",
                          os.path.expanduser("~/vitrine-sa-key.json"))

# ── OpenAI ────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
EMBEDDING_BATCH_SIZE = 250  # max tokens per batch request

GPT_MODEL = "gpt-4o-mini"
GPT_CLUSTER_LABEL_TONE = "luxury_retail"
GPT_DESCRIPTION_WORDS = 50

# ── HDBSCAN ───────────────────────────────────────────────────────────────
HDBSCAN_MIN_CLUSTER_SIZE = 15
HDBSCAN_MIN_SAMPLES = 10

# ── Tables ────────────────────────────────────────────────────────────────
TABLE_CLEAN = f"{PROJECT}.{DATASET}.products_clean"
TABLE_EMBEDDED = f"{PROJECT}.{DATASET}.products_embedded"
TABLE_CLUSTERED = f"{PROJECT}.{DATASET}.products_clustered"
TABLE_ENRICHED = f"{PROJECT}.{DATASET}.products_enriched"
TABLE_RUNS = f"{PROJECT}.{DATASET}.pipeline_runs"
