import re
from pathlib import Path
from typing import Any, Literal

SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = SCRIPT_DIR / "templates"


def load_template(dir_: Literal["css", "parser", "docheader", "inkstone"], name: str, **kwargs: Any) -> str:
    file = TEMPLATE_DIR / dir_ / name
    if not file.exists():
        raise FileNotFoundError(f"Template not found: {file}")
    content = file.read_text(encoding="utf-8")
    for key, value in kwargs.items():
        placeholder = f"<variable>{key}</variable>"
        if not placeholder in content:
            raise ValueError(f"Placeholder '{placeholder}' not found in template '{file}'")
        content = content.replace(placeholder, str(value))
    if re.match(r"<variable>\w+</variable>", content):
        raise ValueError(f"Unreplaced placeholders remain in template '{file}' after substitution")
    return content if content.endswith("\n") else content + "\n"
