"""ATS scoring and AI optimization endpoints."""
import logging

from fastapi import APIRouter
from pymongo.errors import PyMongoError

from app import db
from app.deps import UserId
from app.schemas import AtsScore, JobMatchRequest, OptimizeResponse
from app.services.ats import score_resume
from app.services.optimizer import optimize_resume

log = logging.getLogger(__name__)
router = APIRouter(prefix="/ats", tags=["ats"])


async def _remember_job_description(user_id: str, jd_text: str, score: float) -> None:
    # A DB outage shouldn't throw away a result the user already spent LLM calls on.
    try:
        await db.save_job_description(user_id, jd_text, score)
    except PyMongoError as exc:
        log.warning("Could not store job description for %s: %s", user_id, exc)


@router.post("/score", response_model=AtsScore)
async def score(body: JobMatchRequest, user_id: UserId) -> AtsScore:
    result = await score_resume(body.resume, body.job_description)
    await _remember_job_description(user_id, body.job_description, result.overall_score)
    return result


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize(body: JobMatchRequest, user_id: UserId) -> OptimizeResponse:
    result = await optimize_resume(body.resume, body.job_description)
    await _remember_job_description(user_id, body.job_description, result.final_score.overall_score)
    return result
