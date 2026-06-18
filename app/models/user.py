from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, TimeStampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.auth import RefreshSession
    from app.models.board import Board
    from app.models.task import Task


class User(Base, TimeStampMixin, ActiveMixin, UUIDMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    owned_boards: Mapped[list["Board"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    joined_boards: Mapped[list["Board"]] = relationship(
        secondary="board_members", back_populates="members"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(back_populates="assignee")
