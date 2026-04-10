from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import get_settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import auth, teams, matches, videos, clips, analytics, livestream

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AquaVision Analytics API", version=settings.APP_VERSION)
    yield
    logger.info("Shutting down AquaVision Analytics API")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Water Polo Video Analysis Platform — AI-powered coaching and analytics",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS — permite Vercel, Railway y localhost
origins = settings.ALLOWED_ORIGINS + [
    "https://*.vercel.app",
    "https://*.up.railway.app",
    "http://localhost:3000",
    "http://localhost:80",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production, replace with specific origins list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")
app.include_router(videos.router, prefix="/api/v1")
app.include_router(clips.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(livestream.router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/api/health",
    }


@app.get("/api/v1/queue-status")
async def queue_status():
    from app.services.video_queue import get_queue_status
    return await get_queue_status()
