#!/usr/bin/env bash
# Vitrine GCP project setup — enable APIs, create Artifact Registry
set -euo pipefail

GCLOUD="/c/Users/QURISK/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin/gcloud"
PROJECT_ID="vitrine-wamba-2026"
REGION="eu-west1"

echo "==> Setting active project to ${PROJECT_ID}"
"$GCLOUD" config set project "$PROJECT_ID"

echo "==> Enabling required APIs..."
"$GCLOUD" services enable \
  bigquery.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  sts.googleapis.com \
  --project="$PROJECT_ID"

echo "==> Creating Artifact Registry repository: vitrine-docker"
"$GCLOUD" artifacts repositories create vitrine-docker \
  --project="$PROJECT_ID" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Docker images for Vitrine FastAPI and Pipeline" 2>/dev/null || \
  echo "  (repository already exists — skipping)"

echo "==> Configuring Docker auth for Artifact Registry"
"$GCLOUD" auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> Done. APIs enabled and Artifact Registry ready."
echo "    Registry URL: ${REGION}-docker.pkg.dev/${PROJECT_ID}/vitrine-docker"
