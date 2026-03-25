from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from .account import AccountType


class Refund(Base):
    __tablename__ = "refund"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_acc_em: Mapped[AccountType | None] = mapped_column(SAEnum(AccountType), nullable=True)
    titular_acc_em: Mapped[str] = mapped_column(String(100), nullable=False)
    number_acc_em: Mapped[str] = mapped_column(String(100), nullable=False)
    type_acc_re: Mapped[AccountType | None] = mapped_column(SAEnum(AccountType), nullable=True)
    titular_acc_res: Mapped[str] = mapped_column(String(100), nullable=False)
    number_acc_res: Mapped[str] = mapped_column(String(100), nullable=False)
    code_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __init__(
        self,
        type_acc_em,
        type_acc_re,
        titular_acc_em,
        titular_acc_res,
        number_acc_em,
        number_acc_res,
        value,
        image,
        code_reference,
        created_at=None,
    ):
        self.type_acc_em = type_acc_em
        self.type_acc_re = type_acc_re
        self.code_reference = code_reference
        self.titular_acc_em = titular_acc_em
        self.titular_acc_res = titular_acc_res
        self.number_acc_em = number_acc_em
        self.number_acc_res = number_acc_res
        self.value = value
        self.image = image
        if created_at is not None:
            self.created_at = created_at
