import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OrderStatus(str, enum.Enum):
    pending = "pending"
    generating_text = "generating_text"
    generating_images = "generating_images"
    building_pdf = "building_pdf"
    done = "done"
    failed = "failed"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", native_enum=False),
        default=OrderStatus.pending,
    )
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    theme_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    custom_theme: Mapped[str | None] = mapped_column(String(500), nullable=True)
    style_id: Mapped[str] = mapped_column(String(64))
    child_name: Mapped[str] = mapped_column(String(100))
    child_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    locale: Mapped[str] = mapped_column(String(8), default="ru")

    photo_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pdf_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    preview_keys: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    story_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    character_bible: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(32), default="v2")
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)