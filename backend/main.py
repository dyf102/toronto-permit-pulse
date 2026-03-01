from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.sessions import router as sessions_router
from app.api.parsing import router as parsing_router
from app.api.pipeline import router as pipeline_router
from app.api.export import router as export_router

from contextlib import asynccontextmanager

from app.db.database import engine, Base
from app.models.db_models import PermitSessionDB, DeficiencyItemDB

from sqlalchemy import text

import logging
import sys

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if os.getenv("ENVIRONMENT") == "development" else "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check for GOOGLE_API_KEY on startup
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("FATAL: GOOGLE_API_KEY is not set in the environment.")
        # In production, we might want to exit. In dev, we show a big warning.
        if os.getenv("ENVIRONMENT") != "development":
             sys.exit(1)
        else:
             logger.warning("Running in DEVELOPMENT mode without GOOGLE_API_KEY. Pipeline will fail.")

    # Initialize DB tables on startup
    async with engine.begin() as conn:
        logger.info("Initializing database tables...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialization complete.")
    yield

app = FastAPI(
    title="Permit Pulse Toronto API",
    description="AI-powered permit correction response generator for Garden & Laneway Suites",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the Next.js frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://permit-pulse.ca",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(sessions_router)
app.include_router(parsing_router)
app.include_router(pipeline_router)
app.include_router(export_router)


@app.get("/")
async def root():
    return {
        "service": "Permit Pulse Toronto API",
        "version": "0.1.0",
        "status": "online",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
