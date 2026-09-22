import os

import httpx
import pytest

from test_leads_api import BASE, PK, SUBMIT, ctx, new_lead, ok  # noqa: F401  (ctx is a fixture)

pytestmark = pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="needs TEST_DATABASE_URL")

P = f"{BASE}/api/v1/partners/{PK}"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 50
PLACE = {"location": "Delhi, India", "city": "Delhi", "state": "Delhi", "country": "India", "iso": "IND"}
PAYER = {
    "title": "Mr", "first_name": "Test", "last_name": "Pay", "email": "p@x.com", "phone_code": "91",
    "mobile_number": "9090909090", "date_of_birth": "1990-05-16", "relationship": "Brother",
    "nationality": "India", "nationality_iso": "IND", "birth_place": PLACE, "street_num": "Street",
    "postal_code": "657689", "city": "Delhi", "state": "Delhi", "country": "India", "country_iso": "IND",
    "transfer_amt": "206.40",
}


def upload_ok(doc_id=4480):
    return httpx.Response(200, json={
        "url": "https://e/x.pdf", "message": "File uploaded successfully.", "file_name": "P_1.png",
        "mimetype": "image/png", "o_file_name": "Passport.png", "size": 58, "doc_id": doc_id, "status": True,
    })


async def lead_with_doc(c, mock):
    mock.post(SUBMIT).mock(return_value=ok())
    lead = (await new_lead(c)).json()
    mock.post(f"{P}/documents-upload").mock(return_value=upload_ok())
    r = await c.post(f"/leads/{lead['id']}/documents", data={"doc_key": "passport"}, files={"file": ("Passport.png", PNG, "image/png")})
    return lead, r


async def test_upload_sends_multipart_and_stores_metadata(ctx):
    c, mock = ctx
    lead, r = await lead_with_doc(c, mock)
    assert r.status_code == 201, r.text
    assert r.json()["edubao_doc_id"] == 4480 and r.json()["doc_key"] == "passport" and r.json()["size"] == 58
    sent = mock.calls[-1].request
    assert b'name="doc_key"' in sent.content and b'name="lead_id"' in sent.content and PNG in sent.content
    assert sent.headers["x-api-key"] == "k"
    assert len((await c.get(f"/leads/{lead['id']}/documents")).json()) == 1


async def test_oversize_and_bad_type_never_reach_edubao(ctx):
    c, mock = ctx
    mock.post(SUBMIT).mock(return_value=ok())
    lead = (await new_lead(c)).json()
    upl = mock.post(f"{P}/documents-upload").mock(return_value=upload_ok())
    big = PNG + b"0" * (2 * 1024 * 1024)
    r = await c.post(f"/leads/{lead['id']}/documents", data={"doc_key": "passport"}, files={"file": ("a.png", big, "image/png")})
    assert r.status_code == 413
    r = await c.post(f"/leads/{lead['id']}/documents", data={"doc_key": "passport"}, files={"file": ("a.png", b"GIF89a....", "image/png")})
    assert r.status_code == 415
    r = await c.post(f"/leads/{lead['id']}/documents", data={"doc_key": "../x"}, files={"file": ("a.png", PNG, "image/png")})
    assert r.status_code == 422
    assert upl.call_count == 0


async def test_upload_to_unknown_lead_404(ctx):
    c, _ = ctx
    r = await c.post("/leads/999/documents", data={"doc_key": "passport"}, files={"file": ("a.png", PNG, "image/png")})
    assert r.status_code == 404


async def test_face_and_document_verification(ctx):
    c, mock = ctx
    lead, doc = await lead_with_doc(c, mock)
    face = mock.post(f"{P}/face-verification").mock(return_value=httpx.Response(200, json={"status": True, "verification_status": "matched"}))
    dv = mock.post(f"{P}/document-verification").mock(return_value=httpx.Response(200, json={"status": True, "verification_status": "verified"}))
    files = {"file": ("s.png", PNG, "image/png")}
    r = await c.post(f"/leads/{lead['id']}/verify/face", data={"document_id": doc.json()["id"]}, files=files)
    assert r.status_code == 201 and r.json()["result"] == "matched" and r.json()["type"] == "face"
    body = face.calls[0].request.content
    assert b"CX-1880-BA-1235" in body and b"4480" in body and b"passport" in body and b'name="face"' in body
    r = await c.post(f"/leads/{lead['id']}/verify/document", data={"document_id": doc.json()["id"]}, files=files)
    assert r.json()["result"] == "verified" and b'name="document"' in dv.calls[0].request.content


async def test_verify_with_foreign_document_404(ctx):
    c, mock = ctx
    lead, _ = await lead_with_doc(c, mock)
    r = await c.post(f"/leads/{lead['id']}/verify/face", data={"document_id": 12345}, files={"file": ("s.png", PNG, "image/png")})
    assert r.status_code == 404


async def test_payer_add_then_update_uses_edubao_payer_id(ctx):
    c, mock = ctx
    mock.post(SUBMIT).mock(return_value=ok())
    lead = (await new_lead(c)).json()
    route = mock.post(f"{P}/add-update-payer").mock(
        return_value=httpx.Response(200, json={"message": "payer updated successfully", "payer_id": 709, "account_id": "CX-1880-BA-1235p", "status": True})
    )
    r = await c.put(f"/leads/{lead['id']}/payers", json=PAYER)
    assert r.status_code == 200 and r.json()["edubao_payer_id"] == 709
    first = route.calls[0].request.content.decode().replace(" ", "")
    assert '"birth_place[city]":"Delhi"' in first and '"transfer_amt":"206.40"' in first and '"payer_id":null' in first
    assert f'"lead_id":{lead["edubao_lead_id"]}' in first

    r = await c.put(f"/leads/{lead['id']}/payers", json={**PAYER, "id": r.json()["id"], "first_name": "Changed"})
    assert r.json()["first_name"] == "Changed" and '"payer_id":709' in route.calls[1].request.content.decode().replace(" ", "")
    assert len((await c.get(f"/leads/{lead['id']}/payers")).json()) == 1


async def test_payer_edubao_failure_saves_nothing(ctx):
    c, mock = ctx
    mock.post(SUBMIT).mock(return_value=ok())
    lead = (await new_lead(c)).json()
    mock.post(f"{P}/add-update-payer").mock(return_value=httpx.Response(400, json={"message": "bad payer", "status": False}))
    assert (await c.put(f"/leads/{lead['id']}/payers", json=PAYER)).status_code == 400
    assert (await c.get(f"/leads/{lead['id']}/payers")).json() == []
