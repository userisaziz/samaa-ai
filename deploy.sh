#!/usr/bin/env bash
# ============================================
# SAMAA — Production Deploy to Oracle Cloud
# ============================================
# Uploads code and deploys to Oracle VM
# Uses: Neon PostgreSQL + Upstash Redis + R2
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SSH_KEY="/Users/almabetter/Downloads/ssh-key-2026-06-14.key"
SSH_USER="ubuntu"
SSH_HOST="92.4.87.24"
REMOTE_DIR="/home/ubuntu/xsamaa-ai-pipeline"

echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SAMAA Production Deploy            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# --- Step 1: Verify prerequisites ---
echo -e "${YELLOW}[1/7] Verifying prerequisites...${NC}"

if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}  ✗ SSH key not found: $SSH_KEY${NC}"
    exit 1
fi

if [ ! -f ".env.prod" ]; then
    echo -e "${RED}  ✗ .env.prod not found in current directory${NC}"
    exit 1
fi

chmod 600 "$SSH_KEY"
echo -e "${GREEN}  ✓ Prerequisites verified${NC}"
echo ""

# --- Step 2: Test SSH connection ---
echo -e "${YELLOW}[2/7] Testing SSH connection...${NC}"

if ! ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=15 "$SSH_USER@$SSH_HOST" "echo 'SSH OK'" 2>/dev/null; then
    echo -e "${RED}  ✗ SSH connection failed to $SSH_HOST${NC}"
    echo -e "${RED}    Check: VM running? SSH ingress rule? Firewall?${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ SSH connection works${NC}"
echo ""

# --- Step 3: Create remote directory ---
echo -e "${YELLOW}[3/7] Preparing remote directory...${NC}"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "mkdir -p $REMOTE_DIR"
echo -e "${GREEN}  ✓ Remote directory ready${NC}"
echo ""

# --- Step 4: Upload code ---
echo -e "${YELLOW}[4/7] Uploading code to VM...${NC}"
echo "  This may take a few minutes..."

rsync -avz --delete \
    --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='.git' \
    --exclude='.next' \
    --exclude='__pycache__' \
    --exclude='.DS_Store' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    --exclude='.pytest_cache' \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    ./ "$SSH_USER@$SSH_HOST:$REMOTE_DIR/"

echo -e "${GREEN}  ✓ Code uploaded${NC}"
echo ""

# --- Step 5: Upload .env.prod ---
echo -e "${YELLOW}[5/7] Uploading .env.prod...${NC}"

scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    .env.prod "$SSH_USER@$SSH_HOST:$REMOTE_DIR/.env.prod"

echo -e "${GREEN}  ✓ .env.prod uploaded${NC}"
echo ""

# --- Step 6: Install dependencies and build ---
echo -e "${YELLOW}[6/7] Installing dependencies & building...${NC}"
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" << 'ENDSSH'
set -e
cd /home/ubuntu/xsamaa-ai-pipeline

echo "════════════════════════════════════════"
echo "  🚀 Building Application"
echo "════════════════════════════════════════"
echo ""

# Backend setup
echo "🔧 Setting up Backend..."
cd apps/api

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "  Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "  ✓ uv installed"
fi

# Create venv if needed
if [ ! -d ".venv" ]; then
    echo "  Creating virtual environment..."
    uv venv .venv
fi

source .venv/bin/activate

echo "  Installing Python dependencies..."
uv pip install -e '.[prod]' --quiet 2>/dev/null || uv pip install -e . --quiet
echo "  ✓ Backend ready"
echo ""

# Run migrations (only if DATABASE_URL is set to a real URL)
echo "🗄️ Running database migrations..."
export $(cat ../../.env.prod | grep -v '^#' | xargs) 2>/dev/null || true
if [[ "$DATABASE_URL" == *"neon.tech"* ]] || [[ "$DATABASE_URL" == *"YOUR_"* ]]; then
    if [[ "$DATABASE_URL" == *"YOUR_"* ]]; then
        echo "  ⚠ DATABASE_URL not set — skipping migrations"
        echo "  Edit .env.prod on the VM to add your Neon URL"
    else
        alembic upgrade head 2>&1 | sed 's/^/  /' || echo "  (Migration failed)"
    fi
fi
echo ""

# Frontend setup
echo "🎨 Setting up Frontend..."
cd ../web

# Install Node.js if not present
if ! command -v node &> /dev/null; then
    echo "  Installing Node.js 20..."
    curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
    sudo dnf install -y nodejs
    echo "  ✓ Node.js installed: $(node --version)"
fi

echo "  Installing Node.js dependencies..."
npm install --quiet

echo "  Building Next.js..."
npm run build 2>&1 | tail -10
echo "  ✓ Frontend built"
echo ""

cd ../..
echo "  ✅ Build Complete!"
ENDSSH

echo -e "${GREEN}  ✓ Build successful${NC}"
echo ""

# --- Step 7: Setup systemd services & restart ---
echo -e "${YELLOW}[7/7] Setting up services & restarting...${NC}"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" << 'ENDSSH'
set -e
cd /home/ubuntu/xsamaa-ai-pipeline

# Create systemd services if they don't exist
if ! systemctl list-unit-files 2>/dev/null | grep -q samaa-api; then
    echo "Creating systemd services..."

    # FastAPI service
    sudo tee /etc/systemd/system/samaa-api.service > /dev/null << 'EOF'
[Unit]
Description=SAMAA FastAPI Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/xsamaa-ai-pipeline/apps/api
Environment=PATH=/home/ubuntu/xsamaa-ai-pipeline/apps/api/.venv/bin
ExecStart=/home/ubuntu/xsamaa-ai-pipeline/apps/api/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --env-file ../../.env.prod --workers 1
Restart=always
RestartSec=5
MemoryMax=512M

[Install]
WantedBy=multi-user.target
EOF

    # Celery service
    sudo tee /etc/systemd/system/samaa-celery.service > /dev/null << 'EOF'
[Unit]
Description=SAMAA Celery Worker
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/xsamaa-ai-pipeline/apps/api
Environment=PATH=/home/ubuntu/xsamaa-ai-pipeline/apps/api/.venv/bin
ExecStart=/home/ubuntu/xsamaa-ai-pipeline/apps/api/.venv/bin/celery -A src.workers.celery_app worker --loglevel=info --pool=solo --concurrency=1
EnvironmentFile=/home/ubuntu/xsamaa-ai-pipeline/.env.prod
Restart=always
RestartSec=5
MemoryMax=384M

[Install]
WantedBy=multi-user.target
EOF

    # Next.js service
    sudo tee /etc/systemd/system/samaa-web.service > /dev/null << 'EOF'
[Unit]
Description=SAMAA Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/xsamaa-ai-pipeline/apps/web
ExecStart=/usr/bin/node server.js
Environment=NODE_ENV=production
Environment=PORT=3000
Restart=always
RestartSec=5
MemoryMax=384M

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable samaa-api samaa-celery samaa-web
    echo "✓ Services created and enabled"
fi

# Restart all services
echo "🔄 Restarting services..."
for service in samaa-api samaa-celery samaa-web; do
    sudo systemctl restart $service 2>/dev/null || echo "  ⚠ Failed to restart $service"
    sleep 2
    status=$(systemctl is-active $service 2>/dev/null)
    if [ "$status" = "active" ]; then
        echo "  ✅ $service: running"
    else
        echo "  ❌ $service: $status"
        sudo journalctl -u $service -n 5 --no-pager
    fi
done

# Setup Nginx if not configured
if ! nginx -t 2>&1 | grep -q "successful"; then
    echo "🌐 Configuring Nginx..."
    sudo tee /etc/nginx/conf.d/samaa.conf > /dev/null << 'EOF'
upstream frontend {
    server 127.0.0.1:3000;
}
upstream backend {
    server 127.0.0.1:8000;
}
server {
    listen 80;
    server_name _;
    client_max_body_size 2G;

    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    sudo nginx -t && sudo systemctl restart nginx && sudo systemctl enable nginx
    echo "✓ Nginx configured"
fi

echo ""
echo "════════════════════════════════════════"
echo "  Deployment Complete!"
echo "════════════════════════════════════════"
ENDSSH

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "  🌐 Frontend:   http://$SSH_HOST"
echo "  📝 Backend:    http://$SSH_HOST:8000"
echo "  📖 API Docs:   http://$SSH_HOST:8000/docs"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Wait 10-15 seconds for services to start"
echo "  2. Visit http://$SSH_HOST"
echo "  3. Add Neon DATABASE_URL to .env.prod on the VM if not set"
echo ""
echo -e "${BLUE}SSH Commands:${NC}"
echo "  Connect:  ssh -i '$SSH_KEY' $SSH_USER@$SSH_HOST"
echo "  Logs:     ssh -i '$SSH_KEY' $SSH_USER@$SSH_HOST 'sudo journalctl -u samaa-api -f'"
echo ""
