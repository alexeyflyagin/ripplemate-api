from functools import lru_cache
from pathlib import Path

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"


@lru_cache(maxsize=None)
def _load(name: str) -> str:
    return (_TEMPLATES_DIR / name).read_text(encoding="utf-8")


def render(template_name: str, **context) -> str:
    html = _load(template_name)
    for key, value in context.items():
        html = html.replace("{{" + key + "}}", str(value))
    return html
