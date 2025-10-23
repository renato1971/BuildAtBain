# src/tools/template_loader.py
from pathlib import Path
from typing import List, Type, Optional
from pydantic import BaseModel, Field, field_validator, PrivateAttr
from crewai.tools import BaseTool

class LoadTemplateArgs(BaseModel):
    name: Optional[str] = Field(
        None, description="Template file name, e.g. 'vintage_newsletter.html'"
    )

    @field_validator("name")
    @classmethod
    def safe_name(cls, v):
        if v and ("/" in v or "\\" in v):
            raise ValueError("Invalid template name")
        return v

class TemplateLoaderTool(BaseTool):
    name: str = "template_loader"
    description: str = (
        "Lists and loads HTML templates from the templates folder. "
        "No args: lists templates. With 'name': returns the HTML content."
    )
    args_schema: Type[BaseModel] = LoadTemplateArgs

    # Usamos PrivateAttr para no convertirlo en campo pydantic
    _templates_dir: Path = PrivateAttr(default_factory=lambda: Path("templates"))

    def __init__(self, templates_dir: str = "templates", **data):
        super().__init__(**data)
        self._templates_dir = Path(templates_dir)
        self._templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[str]:
        return sorted([p.name for p in self._templates_dir.glob("*.html")])

    def _run(self, name: Optional[str] = None) -> str:
        if not name:
            files = self.list_templates()
            return "No templates found." if not files else "Available templates: " + ", ".join(files)
        file_path = self._templates_dir / name
        if not file_path.exists():
            return f"Template '{name}' not found. Call without arguments to list options."
        return file_path.read_text(encoding="utf-8")
