from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from core.config import settings


class EncryptionError(Exception):
    """Raised when encryption is misconfigured or a ciphertext can't be decrypted."""


def generate_key() -> str:
    """Create a new Fernet key. Put it in ENCRYPTION_KEYS (see README/.env)."""
    return Fernet.generate_key().decode()


@lru_cache
def _fernet(keys: str) -> MultiFernet:
    parts = [k.strip() for k in keys.split(",") if k.strip()]
    if not parts:
        raise EncryptionError("ENCRYPTION_KEYS is not set")
    try:
        return MultiFernet([Fernet(k) for k in parts])
    except ValueError as exc:
        raise EncryptionError("ENCRYPTION_KEYS contains an invalid Fernet key") from exc


def encrypt(value: str | None) -> str | None:
    """Encrypt a secret for storage in a *_enc column. None passes through."""
    if value is None:
        return None
    return _fernet(settings.encryption_keys).encrypt(value.encode()).decode()


def decrypt(token: str | None) -> str | None:
    if token is None:
        return None
    try:
        return _fernet(settings.encryption_keys).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise EncryptionError("Could not decrypt value (wrong or rotated-out key)") from exc


def rotate(token: str) -> str:
    """Re-encrypt with the newest key; call this when migrating off an old key."""
    try:
        return _fernet(settings.encryption_keys).rotate(token.encode()).decode()
    except InvalidToken as exc:
        raise EncryptionError("Could not rotate value (wrong or rotated-out key)") from exc
