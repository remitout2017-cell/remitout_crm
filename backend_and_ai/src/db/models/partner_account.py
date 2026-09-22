from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin


class PartnerAccount(TimestampMixin, Base):
    """An Edubao partner login. Secret columns (*_enc) hold Fernet ciphertext."""

    __tablename__ = "partner_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    environment: Mapped[str] = mapped_column(String(20), default="staging")  # staging | production
    base_url: Mapped[str] = mapped_column(String(255))
    login_email: Mapped[str] = mapped_column(String(255))
    password_enc: Mapped[str | None] = mapped_column(Text)  # Edubao login password, Fernet ciphertext
    partner_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    user_key: Mapped[str | None] = mapped_column(String(64))
    x_api_key_enc: Mapped[str | None] = mapped_column(Text)
    client_id: Mapped[str | None] = mapped_column(String(128))
    client_secret_enc: Mapped[str | None] = mapped_column(Text)
    access_token_enc: Mapped[str | None] = mapped_column(Text)
    refresh_token_enc: Mapped[str | None] = mapped_column(Text)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @property
    def onboarded(self) -> bool:
        return bool(self.x_api_key_enc and self.client_id and self.client_secret_enc)
