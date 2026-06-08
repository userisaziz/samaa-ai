# SAMAA — Decision Log

**Purpose:** Quick reference for all architectural and technical decisions made during planning.  
**Last Updated:** 2026-06-09  

---

## Decisions

| # | Decision | Choice | Alternatives Considered | Rationale |
|---|---|---|---|---|
| D1 | Starting approach | Full architecture design first, then implement | Start with backend or AI first | System is large, upfront design prevents rework |
| D2 | Repository structure | Monorepo (Turborepo) | Separate repos, hybrid | Shared types between API and frontend, single PR workflow |
| D3 | Backend framework | FastAPI (Python) | NestJS (TypeScript) | AI/ML ecosystem native, better for data pipeline work |
| D4 | ORM | SQLAlchemy 2.0 + Alembic | Prisma (TypeScript-only) | Best Python ORM, async support, mature migration tool |
| D5 | Job queue | Celery + Redis | BullMQ (Node.js), ARQ | Battle-tested for heavy multi-stage pipelines |
| D6 | AI runtime | NVIDIA hosted APIs (NIM) | Self-hosted GPU, alternative LLM APIs | No GPU infra needed for MVP, pay-per-use |
| D7 | File storage | Local FS + storage abstraction | AWS S3, Cloudflare R2 | Fast local dev, abstraction allows swap to S3/R2 later |
| D8 | Deployment | Deferred (Docker-based local dev first) | Multi-service cloud, single provider | Focus on building first, decide deployment later |
| D9 | Frontend framework | Next.js 15 + TypeScript | — (per PRD) | SSR, App Router, great DX |
| D10 | UI components | shadcn/ui + Tailwind CSS | — (per PRD) | Modern, accessible, customizable |
| D11 | State management | Zustand + TanStack Query | Redux Toolkit | Lightweight client state, powerful server state caching |
| D12 | Architecture pattern | FastAPI monolith with Celery workers | API + separate worker service, Python + Node split | Simplest for MVP, can split workers later |
| D13 | Documentation | Plan stored in `plan/` folder as .md files | — | User requested persistent context for future sessions |

---

## Document Index

| File | Purpose |
|---|---|
| `plan/00-architecture-design.md` | Complete system architecture, folder structure, DB schema, API design, AI pipeline, frontend design |
| `plan/01-implementation-plan.md` | Sprint-by-sprint implementation plan with detailed tasks |
| `plan/02-decision-log.md` | This file — all decisions and document index |
| `docs/SAMAA_PRD.md` | Original Product Requirements Document |
