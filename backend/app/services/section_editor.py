"""Per-section AI edits: apply one user instruction to one resume section, leaving the rest untouched."""
import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.errors import AppError
from app.llm import get_llm
from app.schemas import Education, Experience, Lines, Project, SkillGroup, Text
from app.services.prompts import BASE_SYSTEM_PROMPT


class SummarySection(BaseModel):
    summary: Text = ""


class SkillsSection(BaseModel):
    skills: list[SkillGroup] = Field(default_factory=list)


class EducationSection(BaseModel):
    education: list[Education] = Field(default_factory=list)


class AccomplishmentsSection(BaseModel):
    accomplishments: Lines = Field(default_factory=list)


# section_name -> (schema the LLM must return, key that wraps a bare string/list, label for the prompt).
# Structured output needs a JSON object, so bare strings and lists travel wrapped and are unwrapped on return.
_SECTIONS: dict[str, tuple[type[BaseModel], str | None, str]] = {
    "summary": (SummarySection, "summary", "professional summary"),
    "skills": (SkillsSection, "skills", "skills section"),
    "experience_entry": (Experience, None, "one work-experience entry"),
    "project_entry": (Project, None, "one project entry"),
    "education": (EducationSection, "education", "education section"),
    "accomplishments": (AccomplishmentsSection, "accomplishments", "accomplishments list"),
}


async def edit_section(section_name: str, section_data: Any, instruction: str) -> Any:
    model, key, label = _SECTIONS[section_name]
    try:
        current = model.model_validate({key: section_data} if key else section_data)
    except ValidationError as exc:
        first = exc.errors()[0]
        where = ".".join(str(p) for p in first["loc"])
        detail = f"{where}: {first['msg']}" if where else first["msg"]
        raise AppError(
            f"section_data is not a valid {label} ({detail}).", status_code=422, code="invalid_section_data"
        ) from exc

    prompt = (
        f"Section type: {label}\n"
        f"Section data: {current.model_dump_json()}\n"
        f"User instruction: {json.dumps(instruction, ensure_ascii=False)}\n\n"
        "Apply the user's instruction to this section only. Do not change any field\n"
        "or fact not implied by the instruction. Return valid JSON in the same shape\n"
        "as the input section, with only the requested edits applied."
    )
    edited = await get_llm().generate(system=BASE_SYSTEM_PROMPT, prompt=prompt, output_model=model)
    data = edited.model_dump()
    return data[key] if key else data
