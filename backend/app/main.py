from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import setup_logging
from app.api import routes_health, routes_complaints, routes_extraction, routes_chat
from app.db.database import init_db

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router mounting
app.include_router(routes_health.router, prefix=settings.API_PREFIX)
app.include_router(routes_complaints.router, prefix=settings.API_PREFIX)
app.include_router(routes_extraction.router, prefix=settings.API_PREFIX)
app.include_router(routes_chat.router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "health_check": f"{settings.API_PREFIX}/health"
    }
