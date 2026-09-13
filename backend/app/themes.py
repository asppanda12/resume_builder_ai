"""Theme registry. Each id maps to templates/themes/<id>.html."""
from pydantic import BaseModel


class ThemeInfo(BaseModel):
    id: str
    name: str
    description: str


THEMES: dict[str, ThemeInfo] = {
    t.id: t
    for t in [
        ThemeInfo(
            id="sidebar-green",
            name="Sidebar Green",
            description="Two columns: a green sidebar for contact, skills and education; experience on the right.",
        ),
        ThemeInfo(
            id="modern-minimal",
            name="Modern Minimal",
            description="Single column with generous whitespace and thin section rules.",
        ),
        ThemeInfo(
            id="classic-serif",
            name="Classic Serif",
            description="Traditional black-and-white serif layout with no graphics. The most conservative option for ATS.",
        ),
    ]
}

DEFAULT_THEME = "sidebar-green"
