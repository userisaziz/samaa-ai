#!/usr/bin/env bash
# setup-gcp.sh — Bootstrap a GCP project for CXSAMAA Cloud Run deployment
#
# Usage:
#   ./setup-gcp.sh <PROJECT_ID> [REGION]
#
# Example:
#   ./setup-gcp.sh my-cxsamaa-project us-central1
#
# Prerequisites:
#   - gcloud CLI installed and authenticated (gcloud auth login)
#   - An active billing account linked to the project
set -euo pipefail

PROJECT_ID="${1:?Usage: ./setup-gcp.sh <PROJECT_ID> [REGION]}"
REGION="${2:-us-central1}"
SA_NAME="samaa-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="gcp-sa-key.json"

echo "=== CXSAMAA GCP Project Setup ==="
echo "  Project: ${PROJECT_ID}"
echo "  Region:  ${REGION}"
echo ""

# ── Step 1: Set project ─────────────────────────────────────────────────────
echo "[1/5] Setting active project..."
gcloud config set project "${PROJECT_ID}"
echo "  Active project: $(gcloud config get-value project)"

# ── Step 2: Enable required APIs ─────────────────────────────────────────────
echo "[2/5] Enabling required APIs..."
for api in run.googleapis.com build.googleapis.com containerregistry.googleapis.com artifactregistry.googleapis.com; do
  echo "  Enabling ${api}..."
  gcloud services enable "${api}" --project="${PROJECT_ID}" 2>/dev/null || \
    echo "  WARNING: Failed to enable ${api} — check billing is active"
done
echo "  APIs enabled."

# ── Step 3: Create service account ──────────────────────────────────────────
echo "[3/5] Creating service account '${SA_NAME}'..."
if gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "  Service account already exists — skipping creation"
else
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="CXSAMAA Cloud Run Deployer" \
    --project="${PROJECT_ID}"
  echo "  Service account created: ${SA_EMAIL}"
fi

# ── Step 4: Grant roles ─────────────────────────────────────────────────────
echo "[4/5] Granting IAM roles..."
for role in roles/run.admin roles/storage.admin roles/cloudbuild.builds.editor roles/iam.serviceAccountUser; do
  echo "  Granting ${role}..."
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${role}" \
    --condition=None \
    --quiet 2>/dev/null || echo "  WARNING: Failed to grant ${role}"
done
echo "  Roles granted."

# ── Step 5: Generate JSON key ───────────────────────────────────────────────
echo "[5/5] Generating service account key..."
if [ -f "${KEY_FILE}" ]; then
  echo "  ${KEY_FILE} already exists — generating new key with timestamp"
  KEY_FILE="gcp-sa-key-$(date +%Y%m%d%H%M%S).json"
fi

gcloud iam service-accounts keys create "${KEY_FILE}" \
  --iam-account="${SA_EMAIL}" \
  --project="${PROJECT_ID}"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "  Service account key saved to: ${KEY_FILE}"
echo ""
echo "  Next steps:"
echo "  1. Add GCP_PROJECT_ID=${PROJECT_ID} as a GitHub Actions secret"
echo "  2. Add GCP_SA_KEY=<contents of ${KEY_FILE}> as a GitHub Actions secret"
echo "     (base64 encode it: cat ${KEY_FILE} | base64)"
echo "  3. Push to main to trigger deployment"
echo ""
echo "  Manual verification:"
echo "    gcloud run services list --project=${PROJECT_ID} --region=${REGION}"
echo "    gcloud builds list --project=${PROJECT_ID}"
