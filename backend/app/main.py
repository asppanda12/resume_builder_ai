"""FastAPI entry point: `uvicorn app.main:app`."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import db
from app.config import get_settings
from app.errors import register_error_handlers
from app.routers import ats, resume

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.connect(get_settings().mongodb_uri)
    yield
    db.close()


app = FastAPI(title="AI Resume Builder API", version="1.0.0", lifespan=lifespan)
register_error_handlers(app)
app.include_router(resume.router)
app.include_router(ats.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
