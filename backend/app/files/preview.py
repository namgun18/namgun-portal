"""File preview generation (thumbnails, text excerpts)."""

import io
from pathlib import Path

from PIL import Image

# Maximum dimensions for thumbnails
THUMB_MAX = (400, 400)
TEXT_PREVIEW_BYTES = 64 * 1024  # 64KB

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".yml",
    ".py", ".js", ".ts", ".html", ".css", ".sh", ".bat",
    ".log", ".ini", ".toml", ".cfg", ".conf", ".env",
    ".vue", ".jsx", ".tsx", ".sql", ".go", ".rs", ".java",
}
PDF_EXTENSIONS = {".pdf"}


def can_preview(path: Path) -> str | None:
    """Return preview type if file is previewable, else None."""
    ext = path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in TEXT_EXTENSIONS:
        return "text"
    if ext in PDF_EXTENSIONS:
        return "pdf"
    return None


def generate_thumbnail(path: Path) -> bytes | None:
    """Generate a JPEG thumbnail for an image file."""
    ext = path.suffix.lower()
    if ext == ".svg":
        # Return SVG as-is
        return path.read_bytes()

    try:
        with Image.open(path) as img:
            img.thumbnail(THUMB_MAX, Image.Resampling.LANCZOS)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return buf.getvalue()
    except Exception:
        return None


def get_text_preview(path: Path) -> str | None:
    """Read the first portion of a text file."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(TEXT_PREVIEW_BYTES)
    except Exception:
        return None
