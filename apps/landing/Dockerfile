# Multi-stage build for Vite + React landing page
# Build context: repo root (for monorepo workspace resolution)
# Production: nginx serving static dist/ — no Node.js runtime needed

# ── Stage 1: Build ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

# Copy landing page source
COPY apps/landing/package.json apps/landing/package-lock.json* ./apps/landing/

# Install dependencies
WORKDIR /app/apps/landing
RUN npm ci --prefer-offline 2>/dev/null || npm install

# Copy source and build
COPY apps/landing/ ./
RUN npm run build

# ── Stage 2: nginx ───────────────────────────────────────────────────────────
FROM nginx:alpine AS runner

# Copy built assets
COPY --from=builder /app/apps/landing/dist /usr/share/nginx/html

# Custom nginx config: SPA fallback + Cloud Run PORT env var
COPY apps/landing/nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 8080

# nginx:alpine uses this env var for the template
ENV NGINX_PORT=8080
