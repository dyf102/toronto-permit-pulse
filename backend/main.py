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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)
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
