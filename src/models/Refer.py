from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Refer(Base):
    __tablename__ = "refer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_id: Mapped[str] = mapped_column(String(100), ForeignKey("user.google_id"), nullable=False)
    porcentage: Mapped[str] = mapped_column(String(100), nullable=False)
    payment_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("payment.id"), nullable=True)
    refund_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("refund.id"), nullable=True)
    value: Mapped[str] = mapped_column(String(100), nullable=False)

    refund = relationship("Refund", backref="refers", lazy=True)
    payment = relationship("Payment", backref="payments", lazy=True)

    is_pay: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
