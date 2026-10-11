"""Resume CRUD, import, themes, preview and email endpoints."""
from typing import Annotated

from fastapi import APIRouter, File, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, Response

from app import db
from app.deps import UserId
from app.errors import AppError
from app.schemas import (
    EmailRequest,
    EmailResponse,
    PreviewRequest,
    Resume,
    ResumeWithTheme,
    SectionEditRequest,
    SectionEditResponse,
    StoredJobDescription,
    StoredResume,
)
from app.services.emailer import send_resume
from app.services.parser import MAX_PDF_BYTES, parse_resume_pdf
from app.services.renderer import pdf_filename, render_html, render_pdf
from app.services.section_editor import edit_section
from app.themes import THEMES, ThemeInfo

router = APIRouter(tags=["resume"])


@router.post("/resume/parse", response_model=Resume)
async def parse_resume(file: Annotated[UploadFile, File(description="Existing resume as a PDF")]) -> Resume:
    data = await file.read(MAX_PDF_BYTES + 1)
    if not data:
        raise AppError("The uploaded file is empty.", status_code=422, code="empty_file")
    if len(data) > MAX_PDF_BYTES:
        raise AppError("That PDF is larger than 10 MB.", status_code=413, code="file_too_large")
    return await parse_resume_pdf(data)


@router.post("/resume/section/edit", response_model=SectionEditResponse)
async def edit_resume_section(body: SectionEditRequest) -> SectionEditResponse:
    data = await edit_section(body.section_name, body.section_data, body.instruction)
    return SectionEditResponse(section_name=body.section_name, section_data=data)


@router.post("/resume", response_model=StoredResume)
async def save_resume(body: ResumeWithTheme, user_id: UserId) -> StoredResume:
    return await db.save_resume(user_id, body.resume, body.theme)


@router.get("/resume", response_model=StoredResume)
async def get_resume(user_id: UserId) -> StoredResume:
    stored = await db.get_resume(user_id)
    if stored is None:
        raise AppError("No resume saved yet.", status_code=404, code="not_found")
    return stored


# Not in the spec's endpoint list: lets the UI reload the stored "previous JD" (spec §6).
@router.get("/job-description", response_model=StoredJobDescription)
async def get_job_description(user_id: UserId) -> StoredJobDescription:
    stored = await db.get_job_description(user_id)
    if stored is None:
        raise AppError("No job description saved yet.", status_code=404, code="not_found")
    return stored


@router.get("/themes", response_model=list[ThemeInfo])
async def list_themes() -> list[ThemeInfo]:
    return list(THEMES.values())


@router.post(
    "/resume/preview",
    response_class=Response,
    responses={200: {"content": {"text/html": {}, "application/pdf": {}}}},
)
async def preview_resume(body: PreviewRequest) -> Response:
    if body.format == "pdf":
        pdf = await run_in_threadpool(render_pdf, body.resume, body.theme)
        return Response(
            pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{pdf_filename(body.resume)}"'},
        )
    return HTMLResponse(render_html(body.resume, body.theme))


@router.post("/resume/email", response_model=EmailResponse)
async def email_resume(body: EmailRequest) -> EmailResponse:
    pdf = await run_in_threadpool(render_pdf, body.resume, body.theme)
    sent_to = await send_resume(
        to=str(body.to) if body.to else None,
        candidate_name=body.resume.contact.name,
        pdf=pdf,
        filename=pdf_filename(body.resume),
    )
    return EmailResponse(sent_to=sent_to)
