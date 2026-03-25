import uuid

from sqlalchemy import FetchedValue, Integer, String, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, server_default=FetchedValue())
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    idade: Mapped[int] = mapped_column(Integer, nullable=False)


@event.listens_for(User, "before_insert")
def set_uuid_for_non_postgres(_mapper, connection, target) -> None:  # type: ignore[no-untyped-def]
    if getattr(target, "id", None) is None and connection.dialect.name != "postgresql":
        target.id = uuid.uuid4()
