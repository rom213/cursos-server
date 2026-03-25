from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class PaymentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signature: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[str] = mapped_column(String(100), nullable=False)
    google_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("user.google_id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("category.id"), nullable=True)
    status: Mapped[PaymentStatus | None] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    is_refer: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    info_error: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    category = relationship("Category", backref="categories", lazy=True)
