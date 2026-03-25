from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message: Mapped[str] = mapped_column(String(100), nullable=False)
    google_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("user.google_id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("category.id"), nullable=True)
    stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
