"""Theme rendering: Resume -> HTML (Jinja2 templates) -> PDF (WeasyPrint)."""
import re
from pathlib import Path
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.errors import AppError
from app.schemas import Resume

_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"


def _safe_url(url: str) -> str:
    """Allow only http(s)/mailto hrefs (blocks javascript: and friends); bare domains get https://."""
    url = url.strip()
    if not url:
        return ""
    scheme = urlparse(url).scheme.lower()
    if scheme in ("http", "https", "mailto"):
        return url
    if scheme or url.startswith("//"):
        return ""
    return f"https://{url}"


def _display_url(url: str) -> str:
    return re.sub(r"^(https?://)?(www\.)?", "", url.strip()).rstrip("/")


def _date_range(start: str, end: str) -> str:
    return " – ".join(p for p in (start, end) if p)


_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
_env.filters["safe_url"] = _safe_url
_env.filters["display_url"] = _display_url
_env.globals["date_range"] = _date_range


def render_html(resume: Resume, theme: str) -> str:
    return _env.get_template(f"themes/{theme}.html").render(r=resume)


def render_pdf(resume: Resume, theme: str) -> bytes:
    html = render_html(resume, theme)
    try:
        # Imported lazily: WeasyPrint needs the Pango system libraries (bundled in the Docker image),
        # and everything except PDF output should keep working without them.
        from weasyprint import HTML
    except OSError as exc:
        raise AppError(
            "PDF rendering is unavailable because WeasyPrint's system libraries (Pango) aren't installed. See the README.",
            status_code=503,
            code="pdf_unavailable",
        ) from exc
    return HTML(string=html).write_pdf()


def pdf_filename(resume: Resume) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", resume.contact.name).strip("_")
    return f"{slug or 'My'}_Resume.pdf"
