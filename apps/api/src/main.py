from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_v1_router
from src.config import settings

app = FastAPI(
    title="SAMAA API",
    description="Sales Audio Management & AI Analysis - Backend API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/health", tags="Health")
async def health_check():
    return {"status": "healthy", "env": settings.app_env}
