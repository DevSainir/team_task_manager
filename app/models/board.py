import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column as SaColumn
from sqlalchemy import ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimeStampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.column import Column
    from app.models.user import User

board_members = Table(
    "board_members",
    Base.metadata,
    SaColumn("board_id", ForeignKey("boards.id", ondelete="CASCADE"), primary_key=True),
    SaColumn("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Board(Base, TimeStampMixin, UUIDMixin):
    """Database model representing a project board."""

    __tablename__ = "boards"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="owned_boards")
    members: Mapped[list["User"]] = relationship(
        secondary=board_members, back_populates="joined_boards"
    )
    columns: Mapped[list["Column"]] = relationship(
        back_populates="board", cascade="all, delete-orphan", order_by="Column.position"
    )
