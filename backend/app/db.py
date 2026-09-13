"""MongoDB access.

Retention rule (spec §6): one document per user in each collection, and every write
replaces it. No history is ever accumulated.
"""
import logging
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.schemas import Resume, StoredJobDescription, StoredResume

log = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect(uri: str) -> None:
    global _client, _db
    _client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=3000, tz_aware=True)
    _db = _client.get_default_database(default="resume_builder")
    try:
        await _db.resumes.create_index("user_id", unique=True)
        await _db.job_descriptions.create_index("user_id", unique=True)
    except PyMongoError as exc:
        # Keep serving: preview/scoring work without the DB; DB endpoints return 503.
        log.warning("MongoDB unreachable at startup (%s); retrying on each request.", exc)


def close() -> None:
    if _client is not None:
        _client.close()


def _database() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised; connect() runs in the app lifespan")
    return _db


async def save_resume(user_id: str, resume: Resume, theme: str) -> StoredResume:
    doc = {
        "user_id": user_id,
        "resume": resume.model_dump(),
        "theme": theme,
        "updated_at": datetime.now(UTC),
    }
    await _database().resumes.replace_one({"user_id": user_id}, doc, upsert=True)
    return StoredResume.model_validate(doc)


async def get_resume(user_id: str) -> StoredResume | None:
    doc = await _database().resumes.find_one({"user_id": user_id}, {"_id": 0})
    return StoredResume.model_validate(doc) if doc else None


async def save_job_description(user_id: str, jd_text: str, last_score: float) -> None:
    doc = {
        "user_id": user_id,
        "jd_text": jd_text,
        "last_score": last_score,
        "updated_at": datetime.now(UTC),
    }
    await _database().job_descriptions.replace_one({"user_id": user_id}, doc, upsert=True)


async def get_job_description(user_id: str) -> StoredJobDescription | None:
    doc = await _database().job_descriptions.find_one({"user_id": user_id}, {"_id": 0})
    return StoredJobDescription.model_validate(doc) if doc else None
