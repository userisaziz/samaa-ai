# SAMAA — Complete Setup & Developer Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Development Setup](#development-setup)
4. [Data Model & Hierarchy](#data-model--hierarchy)
5. [Audio File Workflow](#audio-file-workflow)
6. [Where Files Live](#where-files-live)
7. [API Workflow (Step-by-Step)](#api-workflow-step-by-step)
8. [AI Processing Pipeline](#ai-processing-pipeline)
9. [Frontend Dashboard](#frontend-dashboard)
10. [Production Setup](#production-setup)
11. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        MONOREPO (Turborepo)                     │
├──────────────────┬──────────────────┬───────────────────────────┤
│   apps/api       │   apps/web       │   packages/shared         │
│   FastAPI        │   Next.js 16     │   TS types + constants    │
│   Python 3.12+   │   React 19       │                           │
│   Port 8000      │   Port 3000      │                           │
├──────────────────┴──────────────────┴───────────────────────────┤
│                                                                 │
│   Infrastructure (Docker Compose):                              │
│   ├── PostgreSQL 16 + pgvector  (port 5432)                     │
│   └── Redis 7                     (port 6379)                   │
│                                                                 │
│   Background Workers:                                           │
│   └── Celery (audio processing pipeline)                        │
│                                                                 │
│   External APIs:                                                │
│   └── NVIDIA NIM (STT, Diarization, LLM Analysis)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Tool | Minimum Version | Check Command |
|------|----------------|---------------|
| Python | 3.12+ | `python3 --version` |
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |
| Docker + Compose | v2+ | `docker compose version` |
| ffmpeg | 6+ | `ffmpeg -version` |
| uv | latest | `uv --version` |

### Install missing prerequisites (macOS)

```bash
brew install python@3.12 node ffmpeg uv
# Docker: download from https://www.docker.com/products/docker-desktop/
```

---

## Development Setup

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd xsamaa-ai-pipeline

# Install Node dependencies (Turborepo + web)
npm install

# Install Python dependencies
cd apps/api
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env
```

Edit `.env` — the critical variables:

```env
# --- Required ---
NVIDIA_API_KEY=nvapi-your-key-here     # Get from https://build.nvidia.com/

# --- Database (defaults work for Docker) ---
DATABASE_URL=postgresql+asyncpg://samaa:samaa_dev_password@localhost:5432/samaa
DATABASE_URL_SYNC=postgresql://samaa:samaa_dev_password@localhost:5432/samaa

# --- Redis ---
REDIS_URL=redis://localhost:6379/0

# --- JWT (change in production!) ---
JWT_SECRET=change-me-to-a-random-secret-in-production

# --- Storage ---
STORAGE_BACKEND=local
LOCAL_UPLOAD_DIR=./uploads

# --- App ---
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:3000
```

### 3. Start Everything

**Option A: One command (recommended)**

```bash
chmod +x start_servers.sh
./start_servers.sh
```

This starts: PostgreSQL, Redis, runs migrations, FastAPI, Celery worker, Next.js.

**Option B: Manual start**

```bash
# Terminal 1: Infrastructure
docker compose up -d

# Terminal 2: Backend API
cd apps/api
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Celery worker (AI pipeline)
cd apps/api
source .venv/bin/activate
celery -A src.workers.celery_app worker --loglevel=info --concurrency=2

# Terminal 4: Frontend
npm run dev:web
```

### 4. Seed Test Data

```bash
cd apps/api
source .venv/bin/activate
python scripts/seed.py
```

This creates:
- **Brand**: RetailMax
- **Stores**: Downtown Flagship, Mall Location
- **Salespeople**: Alice Johnson, Bob Smith, Carol Davis
- **Test login accounts** (see below)

### 5. Verify It Works

| Service | URL | Status |
|---------|-----|--------|
| Frontend | http://localhost:3000 | Open in browser |
| API | http://localhost:8000 | Should return 404 (no route at /) |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API docs |
| API Docs (ReDoc) | http://localhost:8000/redoc | Alternative docs |
| Health Check | http://localhost:8000/health | `{"status": "healthy"}` |

### Test Login Accounts

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@samaa.com | admin123 |
| Brand Admin | brand@retailmax.com | brand123 |
| Store Manager | manager@retailmax.com | manager123 |
| Salesperson | alice@retailmax.com | sales123 |

---

## Data Model & Hierarchy

Every recording is fully traceable through this chain:

```
Brand
  └── Store (1 brand has many stores)
        └── Salesperson (1 store has 2-N salespeople)
              ├── device_number (maps to physical recording device)
              └── Recording (1 salesperson has many recordings)
                    ├── recorded_at (when the conversation happened)
                    ├── uploaded_at (when the file was uploaded)
                    ├── file_url (path to stored audio)
                    └── status (processing pipeline status)
```

### Database Schema

```
brands
├── id (UUID, PK)
├── name (string)
├── description (string, nullable)
├── created_at, updated_at

stores
├── id (UUID, PK)
├── brand_id (FK → brands.id)
├── name (string)
├── location (string, nullable)
├── working_hours (JSONB, nullable)
├── created_at, updated_at

salespeople
├── id (UUID, PK)
├── store_id (FK → stores.id)
├── name (string)
├── email (string, nullable)
├── role (string, nullable)
├── shift (string, nullable)
├── device_number (string, nullable)  ← Maps to physical device
├── created_at, updated_at

recordings
├── id (UUID, PK)
├── salesperson_id (FK → salespeople.id)
├── file_url (text)
├── file_size (bigint, nullable)
├── duration_seconds (int, nullable)
├── format (string: WAV, MP3, M4A)
├── status (enum: UPLOADED → COMPLETED / FAILED)
├── uploaded_at (datetime)
├── recorded_at (datetime, nullable)  ← When conversation happened
├── processed_at (datetime, nullable)
├── silence_gaps (JSONB, nullable)
```

---

## Audio File Workflow

### Input

| Aspect | Detail |
|--------|--------|
| **Accepted formats** | `.wav`, `.mp3`, `.m4a` |
| **Max file size** | No hard limit (practical: up to 2GB) |
| **Upload method** | `POST /api/v1/recordings/upload` (multipart form) |
| **Required fields** | `file` (audio), `salesperson_id` |
| **Optional fields** | `recorded_at` (ISO 8601 datetime) |

### Output (after AI pipeline)

| Output | Where to find it | API Endpoint |
|--------|-----------------|--------------|
| Transcript | `transcript_segments` table | `GET /api/v1/recordings/{id}/transcript` |
| Conversations | `conversations` table | `GET /api/v1/recordings/{id}/conversations` |
| AI Analysis | `conversation_analysis` table | Included in conversations response |
| Scores | `conversation_analysis.scores` JSONB | `GET /api/v1/recordings/{id}/summary` |
| Recording Summary | Aggregated from all conversations | `GET /api/v1/recordings/{id}/summary` |
| CSV Export | Download link | `GET /api/v1/recordings/export/recordings` |

---

## Where Files Live

### Audio Files (Input)

**Development (local storage):**
```
apps/api/uploads/
└── recordings/
    ├── <uuid-1>/
    │   └── ahmed_june9_call1.mp3
    ├── <uuid-2>/
    │   └── sara_june9_call1.wav
    └── <uuid-3>/
        └── omar_june10_call1.m4a
```

Configured via `LOCAL_UPLOAD_DIR=./uploads` in `.env`.

**Production (S3/R2):**
```
s3://your-bucket-name/
└── recordings/
    ├── <uuid-1>/
    │   └── audio.mp3
    └── ...
```

Configured via `STORAGE_BACKEND=s3` + AWS env vars.

### Processed Output (Database)

All AI output lives in PostgreSQL — not as files, but as structured data:

```
PostgreSQL (samaa database)
├── transcript_segments  → word-level timestamps + speaker labels
├── conversations        → segmented conversation blocks
├── conversation_analysis → AI insights (intent, objections, scores)
└── recordings           → status, metadata, file_url reference
```

### Logs

```
.logs/
├── api.log       → FastAPI request logs
├── celery.log    → AI pipeline processing logs
└── web.log       → Next.js build/dev logs
```

---

## API Workflow (Step-by-Step)

### Step 1: Authenticate

```bash
# Login and get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@samaa.com", "password": "admin123"}'

# Save the token
export TOKEN="eyJ..."
```

### Step 2: Create Brand

```bash
curl -X POST http://localhost:8000/api/v1/brands \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Brand", "description": "My retail brand"}'
```

### Step 3: Add Stores

```bash
curl -X POST http://localhost:8000/api/v1/stores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Downtown Store",
    "brand_id": "<brand_id_from_step_2>",
    "location": "123 Main Street"
  }'
```

### Step 4: Add Salespeople (with Device Numbers)

```bash
curl -X POST http://localhost:8000/api/v1/salespeople \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "<store_id>",
    "name": "Ahmed Khan",
    "role": "Senior Sales",
    "shift": "morning",
    "device_number": "DEV-001"
  }'
```

### Step 5: Upload Audio Recordings

```bash
# Upload with recorded_at date
curl -X POST http://localhost:8000/api/v1/recordings/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/recording.mp3" \
  -F "salesperson_id=<salesperson_id>" \
  -F "recorded_at=2025-06-09T14:30:00"
```

### Step 6: Check Processing Status

```bash
# Check status of a recording
curl "http://localhost:8000/api/v1/recordings/<recording_id>/status" \
  -H "Authorization: Bearer $TOKEN"
```

Status flow: `UPLOADED → PREPROCESSING → TRANSCRIBING → DIARIZING → SEGMENTING → ANALYZING → SCORING → COMPLETED`

### Step 7: View Results

```bash
# Get transcript
curl "http://localhost:8000/api/v1/recordings/<id>/transcript" \
  -H "Authorization: Bearer $TOKEN"

# Get AI analysis + scores
curl "http://localhost:8000/api/v1/recordings/<id>/summary" \
  -H "Authorization: Bearer $TOKEN"

# Export as CSV
curl "http://localhost:8000/api/v1/recordings/export/recordings" \
  -H "Authorization: Bearer $TOKEN" -o recordings.csv
```

### Filtering Recordings

```bash
# By date range (day-wise)
GET /api/v1/recordings?date_from=2025-06-09&date_to=2025-06-09T23:59:59

# By salesperson
GET /api/v1/recordings?salesperson_id=<uuid>

# By status
GET /api/v1/recordings?status=COMPLETED

# Combined
GET /api/v1/recordings?salesperson_id=<uuid>&date_from=2025-06-01&date_to=2025-06-30&status=COMPLETED
```

---

## AI Processing Pipeline

When a recording is uploaded, Celery runs this chain automatically:

```
1. PREPROCESSING
   ├── Normalize audio (pydub + ffmpeg)
   ├── Resample to 16kHz mono WAV
   └── Detect silence gaps

2. TRANSCRIPTION (NVIDIA Parakeet STT)
   ├── Speech-to-text with timestamps
   └── Output: word-level segments with start/end times

3. DIARIZATION (NVIDIA NeMo Streusand)
   ├── Speaker identification
   └── Output: speaker labels (SPEAKER_00, SPEAKER_01, ...)

4. SEGMENTATION
   ├── Split into discrete conversations
   ├── Use silence gaps to find boundaries
   └── Output: conversation blocks with time ranges

5. ANALYSIS (NVIDIA Llama 3.3 70B)
   ├── Customer intent detection
   ├── Product mentions
   ├── Budget detection
   ├── Objection identification
   ├── Competitor mentions
   └── Conversation outcome prediction

6. SCORING
   ├── Greeting score
   ├── Discovery score
   ├── Product knowledge score
   ├── Objection handling score
   ├── Closing score
   └── Overall performance score
```

Pipeline config in `celery_app.py`:
- Soft time limit: 1 hour per recording
- Hard time limit: 2 hours
- Concurrency: 2 workers (configurable)
- Task acks late: enabled (won't lose tasks on crash)

---

## Frontend Dashboard

Pages available at http://localhost:3000:

| Page | URL | Description |
|------|-----|-------------|
| Login | `/login` | Authentication |
| Recordings | `/recordings` | List all recordings with filters (status, date range) |
| Recording Detail | `/recordings/[id]` | Transcript, conversations, AI insights |
| Salespeople | `/salespeople` | List with device numbers |
| Salesperson Detail | `/salesperson/[id]` | Performance metrics, recordings |
| Stores | `/stores` | Store list |
| Store Detail | `/store/[id]` | Store metrics |
| Brand | `/brand` | Brand management |
| Search | `/search` | Full-text + semantic search |
| Coaching | `/coaching` | Coaching dashboard |

---

## Production Setup

### Environment Variables (.env)

```env
# --- Database (use managed PostgreSQL with pgvector) ---
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/samaa
DATABASE_URL_SYNC=postgresql://user:pass@host:5432/samaa

# --- Redis (use managed Redis or ElastiCache) ---
REDIS_URL=redis://user:pass@host:6379/0

# --- JWT (USE A STRONG SECRET!) ---
JWT_SECRET=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# --- Storage (S3 or Cloudflare R2) ---
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_S3_BUCKET=samaa-recordings
AWS_S3_REGION=us-east-1
AWS_S3_ENDPOINT=<optional-for-r2>

# --- NVIDIA NIM ---
NVIDIA_API_KEY=nvapi-your-production-key

# --- App ---
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000

# --- CORS (your actual domain) ---
CORS_ORIGINS=https://your-domain.com
```

### Option A: Docker Compose (Single Server)

Create `docker-compose.prod.yml`:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: samaa
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: always

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/samaa
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always

  celery:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    command: celery -A src.workers.celery_app worker --loglevel=warning --concurrency=4
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/samaa
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://your-server-ip:8000/api/v1
    depends_on:
      - api
    restart: always

volumes:
  postgres_data:
  redis_data:
```

Create `apps/api/Dockerfile`:

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install uv && uv pip install --system -e ".[dev]"

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `apps/web/Dockerfile`:

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

Deploy:

```bash
# Build and start
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Seed data (first time only)
docker compose -f docker-compose.prod.yml exec api python scripts/seed.py

# Check logs
docker compose -f docker-compose.prod.yml logs -f api celery web
```

### Option B: Separate Services (Recommended for Scale)

| Service | Where to Host | Notes |
|---------|--------------|-------|
| PostgreSQL | AWS RDS / Supabase / Neon | Must support pgvector extension |
| Redis | AWS ElastiCache / Upstash | For Celery broker + result backend |
| FastAPI | AWS ECS / Railway / Fly.io | Behind a load balancer, 1+ replicas |
| Celery Workers | Same as API or separate | Scale horizontally for more recordings |
| Next.js | Vercel / AWS CloudFront + ECS | Static + SSR |
| Audio Storage | AWS S3 / Cloudflare R2 | Set `STORAGE_BACKEND=s3` |
| NVIDIA NIM | External API | No setup needed, just API key |

### Nginx Reverse Proxy (if self-hosting)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 2G;  # Allow large audio uploads
    }
}
```

### Production Checklist

- [ ] Set `APP_DEBUG=false`
- [ ] Generate strong `JWT_SECRET` (`openssl rand -hex 32`)
- [ ] Set `STORAGE_BACKEND=s3` with proper AWS credentials
- [ ] Use managed PostgreSQL (not Docker)
- [ ] Use managed Redis (not Docker)
- [ ] Set `CORS_ORIGINS` to actual production domain
- [ ] Add HTTPS (Let's Encrypt / Cloudflare)
- [ ] Set `client_max_body_size` in nginx for large uploads
- [ ] Configure Celery concurrency based on CPU cores
- [ ] Set up monitoring (health endpoint: `/health`)
- [ ] Run `alembic upgrade head` on each deployment
- [ ] Back up PostgreSQL regularly

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ffmpeg not found` | `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux) |
| `connection refused :5432` | Docker not running: `docker compose up -d` |
| `connection refused :6379` | Redis not running: `docker compose up -d` |
| Pipeline stuck at UPLOADED | Celery not running: start celery worker |
| Pipeline FAILED | Check `NVIDIA_API_KEY` in `.env` |
| CORS errors | Check `CORS_ORIGINS` matches your frontend URL |
| Upload too large | Increase `client_max_body_size` in nginx |
| Migration fails | Check DB is running, then `alembic upgrade head` |
| Can't import modules | Make sure you're in `apps/api` with venv activated |

### Useful Commands

```bash
# Check API health
curl http://localhost:8000/health

# View Celery logs
tail -f .logs/celery.log

# Check DB tables
docker compose exec postgres psql -U samaa -c "\dt"

# Reset DB (dev only!)
docker compose down -v
docker compose up -d
alembic upgrade head
python scripts/seed.py

# Check recording status
curl "http://localhost:8000/api/v1/recordings?status=FAILED" \
  -H "Authorization: Bearer $TOKEN"

# Reprocess a failed recording
curl -X POST "http://localhost:8000/api/v1/recordings/<id>/reprocess" \
  -H "Authorization: Bearer $TOKEN"
```
