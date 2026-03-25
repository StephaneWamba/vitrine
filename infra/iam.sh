#!/usr/bin/env bash
# Vitrine IAM setup — service accounts + Workload Identity for GitHub Actions
set -euo pipefail

GCLOUD="/c/Users/QURISK/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin/gcloud"
PROJECT_ID="vitrine-wamba-2026"
REGION="eu-west1"
GITHUB_REPO="StephaneWamba/vitrine"

echo "==> Project: ${PROJECT_ID}"

# ─────────────────────────────────────────────────────────────
# Service Account 1: Cloud Run (API + Pipeline)
# ─────────────────────────────────────────────────────────────
SA_CR="vitrine-cloud-run"
SA_CR_EMAIL="${SA_CR}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> Creating service account: ${SA_CR}"
"$GCLOUD" iam service-accounts create "$SA_CR" \
  --project="$PROJECT_ID" \
  --display-name="Vitrine Cloud Run (API + Pipeline)" 2>/dev/null || \
  echo "  (already exists — skipping)"

echo "==> Granting BigQuery roles to ${SA_CR_EMAIL}"
for role in roles/bigquery.dataEditor roles/bigquery.jobUser; do
  "$GCLOUD" projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_CR_EMAIL}" \
    --role="$role" \
    --condition=None \
    --quiet
done

echo "==> Granting Secret Manager access to ${SA_CR_EMAIL}"
"$GCLOUD" projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_CR_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None \
  --quiet

echo "==> Granting Cloud Logging write to ${SA_CR_EMAIL}"
"$GCLOUD" projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_CR_EMAIL}" \
  --role="roles/logging.logWriter" \
  --condition=None \
  --quiet

# ─────────────────────────────────────────────────────────────
# Service Account 2: GitHub Actions deployer
# ─────────────────────────────────────────────────────────────
SA_GHA="github-actions-deployer"
SA_GHA_EMAIL="${SA_GHA}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> Creating service account: ${SA_GHA}"
"$GCLOUD" iam service-accounts create "$SA_GHA" \
  --project="$PROJECT_ID" \
  --display-name="GitHub Actions CI/CD Deployer" 2>/dev/null || \
  echo "  (already exists — skipping)"

echo "==> Granting Cloud Run admin to ${SA_GHA_EMAIL}"
"$GCLOUD" projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_GHA_EMAIL}" \
  --role="roles/run.admin" \
  --condition=None \
  --quiet

"$GCLOUD" projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_GHA_EMAIL}" \
  --role="roles/artifactregistry.writer" \
  --condition=None \
  --quiet

"$GCLOUD" projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_GHA_EMAIL}" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None \
  --quiet

# ─────────────────────────────────────────────────────────────
# Workload Identity Federation for GitHub Actions (keyless)
# ─────────────────────────────────────────────────────────────
echo "==> Creating Workload Identity Pool: github-pool"
"$GCLOUD" iam workload-identity-pools create "github-pool" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool" 2>/dev/null || \
  echo "  (pool already exists — skipping)"

echo "==> Creating OIDC provider: github-provider"
"$GCLOUD" iam workload-identity-pools providers create-oidc "github-provider" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub OIDC Provider" \
  --attribute-mapping="google.subject=assertion.sub,assertion.repository=assertion.repository,assertion.repository_owner=assertion.repository_owner" \
  --issuer-uri="https://token.actions.githubusercontent.com" 2>/dev/null || \
  echo "  (provider already exists — skipping)"

WIF_POOL=$("$GCLOUD" iam workload-identity-pools describe "github-pool" \
  --project="$PROJECT_ID" \
  --location="global" \
  --format='value(name)')

WIF_PROVIDER="${WIF_POOL}/providers/github-provider"

echo "==> Binding Workload Identity to GitHub repo: ${GITHUB_REPO}"
"$GCLOUD" iam service-accounts add-iam-policy-binding "$SA_GHA_EMAIL" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WIF_POOL}/attribute.repository/${GITHUB_REPO}" \
  --quiet

echo ""
echo "==> IAM setup complete. Add these to GitHub Actions secrets:"
echo "    GCP_PROJECT_ID=${PROJECT_ID}"
echo "    GCP_WORKLOAD_IDENTITY_PROVIDER=${WIF_PROVIDER}"
echo "    GCP_SERVICE_ACCOUNT=${SA_GHA_EMAIL}"
echo "    GCP_CLOUD_RUN_SA=${SA_CR_EMAIL}"
