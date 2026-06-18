import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimeStampMixin, UUIDMixin
from app.models.enums import PriorityEnum

if TYPE_CHECKING:
    from app.models.column import Column
    from app.models.user import User


class Task(Base, TimeStampMixin, UUIDMixin):
    """Database model representing a task."""

    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[PriorityEnum] = mapped_column(
        Enum(PriorityEnum), default=PriorityEnum.medium, nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    attachment_urls: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    column_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("columns.id", ondelete="CASCADE"), nullable=False
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    column: Mapped["Column"] = relationship(back_populates="tasks")
    assignee: Mapped["User | None"] = relationship(back_populates="assigned_tasks")
