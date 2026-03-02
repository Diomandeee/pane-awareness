"""Title to filesystem-safe slug conversion."""

import re
import unicodedata

from .config import MAX_TITLE_LENGTH


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug.

    - Normalizes unicode
    - Lowercases
    - Replaces non-alphanumeric chars with hyphens
    - Collapses multiple hyphens
    - Strips leading/trailing hyphens
    - Truncates to MAX_TITLE_LENGTH
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    if len(text) > MAX_TITLE_LENGTH:
        cut = text[:MAX_TITLE_LENGTH].rfind("-")
        if cut > 20:
            text = text[:cut]
        else:
            text = text[:MAX_TITLE_LENGTH]
    return text or "untitled"
