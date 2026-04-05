from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base, db


class PaymentRegister(Base):
    __tablename__ = "payment_register"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pay_val: Mapped[str] = mapped_column(String(100), nullable=False)
    google_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("user.google_id"), nullable=True)
    google_id_refer: Mapped[str | None] = mapped_column(String(100), ForeignKey("user.google_id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("category.id"), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    codeValue: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "complated", "error", "refunded", name="status_enum"),
        default="pending",
        nullable=False,
    )

    def cambiarStatus(self, status="complated"):
        self.status = status
        db.session.commit()
