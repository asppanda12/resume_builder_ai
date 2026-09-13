"""Pydantic models: the canonical resume object (spec §5) and the API request/response bodies."""
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, EmailStr, Field, StringConstraints

from app.themes import DEFAULT_THEME, THEMES

Text = Annotated[str, StringConstraints(strip_whitespace=True)]


def _drop_blank(items: list[str]) -> list[str]:
    return [s.strip() for s in items if s.strip()]


# The form edits bullets as raw textarea lines, so blanks are dropped on the way in.
Lines = Annotated[list[str], AfterValidator(_drop_blank)]


def _known_theme(theme: str) -> str:
    if theme not in THEMES:
        raise ValueError(f"unknown theme '{theme}'; choose one of: {', '.join(THEMES)}")
    return theme


ThemeId = Annotated[str, AfterValidator(_known_theme)]
JobDescriptionText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=30, max_length=30_000)
]


# --- Resume schema (spec §5) ---------------------------------------------------


class Link(BaseModel):
    label: Text = ""
    url: Text = ""


class Contact(BaseModel):
    name: Text = ""
    location: Text = ""
    phone: Text = ""
    email: Text = ""
    links: list[Link] = Field(default_factory=list)


class SkillGroup(BaseModel):
    category: Text = ""
    items: Lines = Field(default_factory=list)


class Experience(BaseModel):
    company: Text = ""
    title: Text = ""
    location: Text = ""
    start: Text = ""
    end: Text = ""
    bullets: Lines = Field(default_factory=list)


class Education(BaseModel):
    institution: Text = ""
    degree: Text = ""
    date: Text = ""
    gpa: Text = ""


class Project(BaseModel):
    name: Text = ""
    stack: Text = ""
    bullets: Lines = Field(default_factory=list)


class Resume(BaseModel):
    contact: Contact = Field(default_factory=Contact)
    summary: Text = ""
    skills: list[SkillGroup] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    accomplishments: Lines = Field(default_factory=list)


# --- Requests -------------------------------------------------------------------


class ResumeWithTheme(BaseModel):
    resume: Resume
    theme: ThemeId = DEFAULT_THEME


class PreviewRequest(ResumeWithTheme):
    format: Literal["html", "pdf"] = "html"


class EmailRequest(ResumeWithTheme):
    # Assumption: "the user's Gmail" is the configured GMAIL_ADDRESS unless another recipient is given.
    to: EmailStr | None = None


class JobMatchRequest(BaseModel):
    resume: Resume
    job_description: JobDescriptionText


# --- Responses ------------------------------------------------------------------


class StoredResume(BaseModel):
    resume: Resume
    theme: str
    updated_at: datetime


class StoredJobDescription(BaseModel):
    jd_text: str
    last_score: float | None = None
    updated_at: datetime


class AtsScore(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    keyword_score: float = Field(ge=0, le=100)
    semantic_score: float = Field(ge=0, le=100)
    matched_keywords: list[str]
    missing_keywords: list[str]
    suggestions: list[str] = Field(default_factory=list)
    threshold: float
    meets_threshold: bool


class OptimizeResponse(BaseModel):
    mode: Literal["improve", "gate"]
    optimized: bool
    iterations: int
    message: str
    original_score: AtsScore
    final_score: AtsScore
    resume: Resume


class EmailResponse(BaseModel):
    sent_to: str
