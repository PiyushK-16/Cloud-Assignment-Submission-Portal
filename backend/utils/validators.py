"""Input + file validation helpers."""
import os
import re
import uuid

from backend.utils.errors import ServiceError

MASTER_ALLOWED = {"pdf", "docx", "zip", "png", "jpg", "jpeg", "txt"}

# Magic numbers: the first bytes of a real file of that type (an extension alone is easy to fake)
SIGNATURES = {
    "pdf": [b"%PDF"],
    "docx": [b"PK\x03\x04"],
    "zip": [b"PK\x03\x04"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
}

CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "zip": "application/zip",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "txt": "text/plain",
}


def validate_password(pw: str) -> None:
    if len(pw) < 8 or not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        raise ServiceError(422, "Password must be at least 8 characters and contain a letter and a digit.")


def parse_allowed_types(csv: str) -> list[str]:
    types = [t.strip().lower().lstrip(".") for t in csv.split(",") if t.strip()]
    if not types:
        raise ServiceError(422, "At least one allowed file type is required.")
    bad = [t for t in types if t not in MASTER_ALLOWED]
    if bad:
        raise ServiceError(422, f"Unsupported file types: {', '.join(bad)}. Allowed: {', '.join(sorted(MASTER_ALLOWED))}")
    return types


def extension_of(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower().lstrip(".")


def safe_filename(filename: str) -> str:
    """Strip path components and unsafe characters (prevents path traversal such as ../../etc/passwd)."""
    base = os.path.basename((filename or "file").replace("\\", "/"))
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._") or "file"
    return base[:100]


def validate_upload(filename: str, data: bytes, allowed_types: list[str]) -> str:
    ext = extension_of(filename)
    if ext not in allowed_types:
        raise ServiceError(415, f"File type '.{ext}' not allowed. Allowed: {', '.join(allowed_types)}")
    if not data:
        raise ServiceError(422, "Uploaded file is empty.")
    sigs = SIGNATURES.get(ext)
    if sigs and not any(data.startswith(s) for s in sigs):
        raise ServiceError(415, f"File content does not match its '.{ext}' extension.")
    if ext == "txt" and b"\x00" in data[:2048]:
        raise ServiceError(415, "File content does not look like plain text.")
    return ext


def new_id() -> str:
    return uuid.uuid4().hex
