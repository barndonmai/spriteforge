from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True, default="queued")
    stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    requested_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    resolved_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_size: Mapped[int] = mapped_column(Integer, nullable=False, default=64)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_image_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    manifest_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    zip_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    reference_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

