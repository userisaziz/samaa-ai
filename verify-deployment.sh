#!/bin/bash
# verify-deployment.sh — Verify both fixes are applied correctly

set -e

echo "════════════════════════════════════════"
echo "  Deployment Verification Script"
echo "════════════════════════════════════════"
echo ""

PROJECT="samaa-production-2026"
REGION="us-central1"

# ── Check 1: Artifact Registry Permissions ─────────────────────────
echo "✓ Check 1: Cloud Build Artifact Registry permissions"
POLICY=$(gcloud artifacts repositories get-iam-policy samaa-images \
  --location=${REGION} \
  --format="value(bindings.role)" \
  --filter="bindings.members:serviceAccount:939378489002@cloudbuild.gserviceaccount.com" 2>&1)

if echo "$POLICY" | grep -q "artifactregistry.writer"; then
  echo "  ✅ Cloud Build has artifactregistry.writer role"
else
  echo "  ❌ Missing artifactregistry.writer role"
  echo "  Fix: Run the IAM binding command from the deployment fix"
  exit 1
fi

echo ""

# ── Check 2: Secret Manager WEB_ENV_PROD ───────────────────────────
echo "✓ Check 2: WEB_ENV_PROD secret contains API_BASE_URL"
SECRET_CONTENT=$(gcloud secrets versions access latest \
  --secret=web-env-prod \
  --project=${PROJECT} 2>&1)

if echo "$SECRET_CONTENT" | grep -q "API_BASE_URL"; then
  echo "  ✅ API_BASE_URL found in secret"
  API_URL=$(echo "$SECRET_CONTENT" | grep "API_BASE_URL" | cut -d'=' -f2)
  echo "  Value: ${API_URL}"
else
  echo "  ⚠️  API_BASE_URL not in secret (will be added by cloudbuild.yaml)"
  echo "  Note: This is okay — the build script will auto-add it"
fi

echo ""

# ── Check 3: Cloud Build Config ────────────────────────────────────
echo "✓ Check 3: cloudbuild.yaml has improved API_BASE_URL handling"
if grep -q "Added new API_BASE_URL" cloudbuild.yaml; then
  echo "  ✅ Build config will add API_BASE_URL if missing"
else
  echo "  ❌ Build config missing fallback logic"
  exit 1
fi

echo ""

# ── Check 4: Cloud Run Service Status ─────────────────────────────
echo "✓ Check 4: Cloud Run services status"
for SERVICE in samaa-api samaa-web samaa-landing; do
  STATUS=$(gcloud run services describe ${SERVICE} \
    --region=${REGION} \
    --project=${PROJECT} \
    --format="value(status.conditions[0].status)" 2>&1 || echo "NOT_FOUND")
  
  if [ "$STATUS" = "True" ]; then
    URL=$(gcloud run services describe ${SERVICE} \
      --region=${REGION} \
      --project=${PROJECT} \
      --format="value(status.url)")
    echo "  ✅ ${SERVICE}: READY (${URL})"
  else
    echo "  ⚠️  ${SERVICE}: ${STATUS} (may need deployment)"
  fi
done

echo ""
echo "════════════════════════════════════════"
echo "  Verification Complete"
echo "════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Commit the cloudbuild.yaml changes"
echo "  2. Push to main to trigger deployment"
echo "  3. Monitor: gcloud builds list --limit=3"
echo ""
