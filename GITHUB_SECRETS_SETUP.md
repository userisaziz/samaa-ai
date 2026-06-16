# GitHub Secrets Setup Guide

## ✅ Completed: GCP Workload Identity Federation

Your GCP is now configured with **Workload Identity Federation** - no service account key needed!

### What's Already Done:
- ✅ Service account created: `github-deployer@cxsamaa.iam.gserviceaccount.com`
- ✅ Workload Identity Pool: `github-pool`
- ✅ OIDC Provider: `github-provider` (restricted to `userisaziz/samaa-ai` repo)
- ✅ Required permissions granted (Cloud Run, Cloud Build, Storage, IAM)
- ✅ GitHub Actions workflow updated to use Workload Identity

---

## 🔧 Remaining: Add GitHub Repository Secrets

You need to add these secrets to your GitHub repository:

### Go to:
```
https://github.com/userisaziz/samaa-ai/settings/secrets/actions
```

### Required Secrets:

| Secret Name | Description | Where to Find It |
|-------------|-------------|------------------|
| `GCP_PROJECT_ID` | Your GCP project ID | Already know: `cxsamaa` |
| `NEON_DATABASE_URL` | PostgreSQL connection string (async) | From Neon dashboard |
| `NEON_DATABASE_URL_SYNC` | PostgreSQL connection string (sync) | From Neon dashboard |
| `JWT_SECRET` | Secret key for JWT signing | Generate: `openssl rand -hex 32` |
| `R2_ACCOUNT_ID` | Cloudflare R2 account ID | Cloudflare R2 dashboard |
| `R2_ACCESS_KEY_ID` | R2 access key | Cloudflare R2 > API Tokens |
| `R2_SECRET_ACCESS_KEY` | R2 secret key | Cloudflare R2 > API Tokens |
| `R2_BUCKET` | R2 bucket name | Your bucket name |
| `CORS_ORIGINS` | Allowed CORS origins | e.g., `https://samaa-web-xxxxx-uc.a.run.app,https://cxsamaa.store` |

### Optional Secrets:
| Secret Name | Description |
|-------------|-------------|
| `API_BASE_URL` | API base URL (if different from Cloud Run URL) |

---

## 📋 Quick Setup Commands

### Generate JWT Secret:
```bash
openssl rand -hex 32
```

### Get Neon Database URLs:
1. Go to https://console.neon.tech
2. Select your project
3. Copy connection string (async): `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/dbname`
4. For sync URL, replace protocol with `postgresql+psycopg2://`

### Get R2 Credentials:
1. Go to Cloudflare Dashboard > R2 Storage
2. Create API Token with "Admin Read & Write" permissions
3. Copy Account ID, Access Key ID, and Secret Access Key
4. Create a bucket (e.g., `samaa-audio`)

---

## 🚀 After Adding Secrets

Once you've added all the secrets, the deployment will work automatically:

1. Push to main branch
2. GitHub Actions will trigger
3. Build Docker images (API, Web, Landing)
4. Deploy to Cloud Run
5. Run health checks
6. Done! ✅

### Test the Deployment:
```bash
git commit -m "fix: update workflow for workload identity" -a
git push origin main
```

---

## 🔍 Monitor Deployment

Watch the deployment progress:
```bash
# View workflow runs
gh run list --workflow=deploy-gcp.yml

# View specific run logs
gh run view <RUN_ID> --log

# Or visit:
# https://github.com/userisaziz/samaa-ai/actions
```

---

## 📝 Notes

- **Workload Identity Federation** is more secure than service account keys
- Keys cannot be leaked or stolen
- Access is restricted to your specific GitHub repository
- Automatic credential rotation
- No secrets to manage for GCP authentication
