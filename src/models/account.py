import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class AccountType(enum.Enum):
    nequi = "nequi"
    daviplata = "daviplata"
    llave = "llave"


class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_acc: Mapped[AccountType] = mapped_column(SAEnum(AccountType), nullable=False)
    number_acc: Mapped[str] = mapped_column(String(100), nullable=False)
    google_id: Mapped[str] = mapped_column(String(100), ForeignKey("user.google_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name_acc": self.name_acc.value,
            "number_acc": self.number_acc,
        }
