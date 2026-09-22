import io

import pytest
from fastapi import HTTPException, UploadFile

from app.uploads import read_upload
from core.config import settings

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def upload(content: bytes, name="Pass port.png") -> UploadFile:
    return UploadFile(io.BytesIO(content), filename=name)


async def test_valid_types_sniffed_from_content():
    assert (await read_upload(upload(PNG))).mimetype == "image/png"
    assert (await read_upload(upload(b"%PDF-1.4 x", "a.bin"))).filename == "a.pdf"
    assert (await read_upload(upload(b"\xff\xd8\xff\xe0abc", "x.jpeg"))).mimetype == "image/jpeg"


async def test_filename_sanitized():
    up = await read_upload(upload(PNG, "../../etc/pass wd?.png"))
    assert up.filename == "pass_wd_.png"


async def test_exactly_2mb_ok_and_over_rejected():
    limit = settings.max_upload_bytes
    assert limit == 2 * 1024 * 1024
    ok = await read_upload(upload(PNG + b"0" * (limit - len(PNG))))
    assert ok.size == limit
    with pytest.raises(HTTPException) as ei:
        await read_upload(upload(PNG + b"0" * (limit - len(PNG) + 1)))
    assert ei.value.status_code == 413


async def test_wrong_type_and_empty_rejected():
    with pytest.raises(HTTPException) as ei:
        await read_upload(upload(b"MZ\x90\x00 exe pretending", "evil.png"))
    assert ei.value.status_code == 415
    with pytest.raises(HTTPException) as ei:
        await read_upload(upload(b""))
    assert ei.value.status_code == 422
