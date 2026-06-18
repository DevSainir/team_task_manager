import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimeStampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.board import Board
    from app.models.task import Task


class Column(Base, TimeStampMixin, UUIDMixin):
    """Database model representing a column within a board."""

    __tablename__ = "columns"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    board_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), nullable=False
    )

    board: Mapped["Board"] = relationship(back_populates="columns")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="column", cascade="all, delete-orphan", order_by="Task.position"
    )
