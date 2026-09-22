import re
from dataclasses import dataclass

from fastapi import HTTPException, UploadFile

from core.config import settings

# Content is sniffed from magic bytes; the client-supplied Content-Type is not trusted.
_SIGNATURES = [
    (b"%PDF-", "application/pdf", "pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
]


@dataclass
class ValidUpload:
    filename: str
    content: bytes
    mimetype: str

    @property
    def size(self) -> int:
        return len(self.content)

    def as_tuple(self) -> tuple[str, bytes, str]:
        return (self.filename, self.content, self.mimetype)


async def read_upload(file: UploadFile) -> ValidUpload:
    """Read an upload fully into memory, enforcing the size cap and allowed types (PDF/PNG/JPEG)."""
    limit = settings.max_upload_bytes
    content = await file.read(limit + 1)  # never buffer more than the cap
    if len(content) > limit:
        raise HTTPException(413, f"File exceeds the {limit // (1024 * 1024)} MB limit")
    if not content:
        raise HTTPException(422, "File is empty")
    for magic, mimetype, ext in _SIGNATURES:
        if content.startswith(magic):
            stem = re.sub(r"[^A-Za-z0-9._-]", "_", (file.filename or "upload").rsplit("/", 1)[-1])
            stem = stem.rsplit(".", 1)[0] or "upload"
            return ValidUpload(f"{stem}.{ext}", content, mimetype)
    raise HTTPException(415, "Only PDF, PNG and JPEG files are allowed")
