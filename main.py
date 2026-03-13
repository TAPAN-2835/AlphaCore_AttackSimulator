from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import engine, Base

# Import all models so Alembic/Base.metadata sees them
import auth.models  # noqa: F401
import campaigns.models  # noqa: F401
import events.models  # noqa: F401
import analytics.models  # noqa: F401

# Routers
from auth.routes import router as auth_router
from campaigns.routes import router as campaigns_router
from simulation.routes import router as simulation_router
from analytics.routes import router as analytics_router
from admin.routes import router as admin_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables (for hackathon convenience — use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Breach — Phishing Simulation Platform",
    description=(
        "Production-grade API for phishing awareness campaigns, "
        "event tracking, and risk analytics."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth_router,       prefix="/auth",       tags=["Auth"])
app.include_router(campaigns_router,  prefix="/campaigns",  tags=["Campaigns"])
app.include_router(simulation_router, prefix="/sim",        tags=["Simulation"])
app.include_router(analytics_router,  prefix="/analytics",  tags=["Analytics"])
app.include_router(admin_router,      prefix="/admin",      tags=["Admin"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
