# Landing Page Deployment Guide

## Quick Start

The landing page (`samaa-landing`) is now fully configured for deployment to Cloud Run and will be accessible at `https://cxsamaa.store`.

## What's Configured

### 1. Build & Deployment Pipeline
- ✅ **Dockerfile**: Multi-stage build (Vite → nginx) at `apps/landing/Dockerfile`
- ✅ **Cloud Build**: Build/push/deploy steps added to `cloudbuild.yaml`
- ✅ **GitHub Actions**: Health check added to `.github/workflows/deploy-gcp.yml`
- ✅ **Manual Deploy**: Step 8/9 added to `deploy.sh`

### 2. Service Configuration
- **Service Name**: `samaa-landing`
- **Port**: 8080 (nginx)
- **Resources**: 1 CPU, 256MB RAM
- **Concurrency**: 100
- **Timeout**: 30s
- **Scaling**: 0-3 instances

### 3. Domain Mapping
- **Root Domain**: `cxsamaa.store` → `samaa-landing`
- **Dashboard**: `app.cxsamaa.store` → `samaa-web`
- **API**: `api.cxsamaa.store` → `samaa-api`

## Deploy Now

### Option A: Push to Main (CI/CD)
```bash
git add -A
git commit -m "feat: add landing page deployment and domain mappings"
git push origin main
```

The GitHub Actions workflow will automatically:
1. Build the landing page Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run as `samaa-landing`
4. Verify service readiness

### Option B: Manual Deploy
```bash
./deploy.sh
```

This will deploy all 4 services (API, Web, Worker, Landing) and set up domain mappings.

## DNS Configuration Required

After deployment, you need to configure DNS at your domain registrar:

### For `cxsamaa.store` (Landing Page)
```
Type: A
Name: @
Value: [Get from GCP Console after domain mapping]
TTL: 300
```

### For `app.cxsamaa.store` (Dashboard)
```
Type: CNAME
Name: app
Value: ghs.googlehosted.com
TTL: 300
```

### For `api.cxsamaa.store` (API)
```
Type: CNAME
Name: api
Value: ghs.googlehosted.com
TTL: 300
```

## Create Domain Mappings

If using manual deploy, the script will create these automatically. Otherwise:

```bash
# Landing page (root domain)
gcloud beta run domain-mappings create \
  --service=samaa-landing \
  --domain=cxsamaa.store \
  --region=us-central1

# Dashboard (app subdomain)
gcloud beta run domain-mappings create \
  --service=samaa-web \
  --domain=app.cxsamaa.store \
  --region=us-central1

# API (api subdomain)
gcloud beta run domain-mappings create \
  --service=samaa-api \
  --domain=api.cxsamaa.store \
  --region=us-central1
```

## Verify Deployment

```bash
# Check all services
gcloud run services list --region=us-central1

# Check domain mappings
gcloud beta run domain-mappings list --region=us-central1

# Test endpoints (after DNS propagation)
curl -I https://cxsamaa.store
curl -I https://app.cxsamaa.store
curl -I https://api.cxsamaa.store
```

## Timeline

1. **Deployment**: ~3-5 minutes (CI/CD build + deploy)
2. **Domain Mapping**: ~1-2 minutes
3. **DNS Propagation**: 5-30 minutes
4. **SSL Certificate**: 10-30 minutes (automatic)

## Troubleshooting

### Landing page not accessible
- Verify service is deployed: `gcloud run services describe samaa-landing --region=us-central1`
- Check logs: `gcloud run services logs read samaa-landing --region=us-central1`

### Domain mapping fails
- Ensure domain is verified in GCP Console
- Check org policy allows domain mappings
- Verify DNS records are correct

### SSL certificate pending
- Wait 10-30 minutes
- Verify DNS records match Google's requirements
- Check domain verification status in GCP Console

## Next Steps

After landing page is live:
1. Test all three domains work correctly
2. Update CORS origins if needed
3. Set up CDN caching for landing page
4. Configure monitoring/alerting
5. Add analytics tracking to landing page
