"""
FastAPI application entry point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import auth, products, templates, competitors, matches, crawl, dashboard, images

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Competitive Edge Engine API",
    description="Generic competitive intelligence platform API",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup"""
    if not settings.OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is not set in environment variables!")
        logger.error("Please set OPENROUTER_API_KEY in your .env file")
    else:
        logger.info(f"OpenRouter API key configured (length: {len(settings.OPENROUTER_API_KEY)})")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(templates.router, prefix=settings.API_V1_PREFIX)
app.include_router(competitors.router, prefix=settings.API_V1_PREFIX)
app.include_router(matches.router, prefix=settings.API_V1_PREFIX)
app.include_router(crawl.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(images.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {"message": "Competitive Edge Engine API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
