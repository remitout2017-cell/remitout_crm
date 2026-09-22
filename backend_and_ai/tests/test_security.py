import pytest
from cryptography.fernet import Fernet

from core import security
from core.config import settings


@pytest.fixture
def keys(monkeypatch):
    def _set(*ks):
        monkeypatch.setattr(settings, "encryption_keys", ",".join(ks))
    return _set


def test_roundtrip(keys):
    keys(Fernet.generate_key().decode())
    token = security.encrypt("client-secret")
    assert token != "client-secret"
    assert security.decrypt(token) == "client-secret"


def test_none_passthrough(keys):
    keys(Fernet.generate_key().decode())
    assert security.encrypt(None) is None
    assert security.decrypt(None) is None


def test_missing_key_raises(keys):
    keys()
    with pytest.raises(security.EncryptionError):
        security.encrypt("x")


def test_invalid_key_raises(keys):
    keys("not-a-key")
    with pytest.raises(security.EncryptionError):
        security.encrypt("x")


def test_wrong_key_raises(keys):
    keys(Fernet.generate_key().decode())
    token = security.encrypt("x")
    keys(Fernet.generate_key().decode())
    with pytest.raises(security.EncryptionError):
        security.decrypt(token)


def test_key_rotation(keys):
    old, new = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    keys(old)
    token = security.encrypt("x")
    keys(new, old)  # new key first, old still decrypts
    assert security.decrypt(token) == "x"
    rotated = security.rotate(token)
    keys(new)  # old key dropped
    assert security.decrypt(rotated) == "x"
