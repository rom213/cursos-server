import hashlib
import random
from datetime import datetime, timedelta

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)

    def __init__(self, email, code=None):
        self.email = hashlib.sha256(email.encode()).hexdigest()
        raw_code = code if code else "".join([str(random.randint(0, 9)) for _ in range(6)])
        self.code = hashlib.sha256(raw_code.encode()).hexdigest()
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(minutes=3)
        self.is_used = False
        self.raw_code = raw_code

    def is_valid(self):
        return not self.is_used and datetime.utcnow() < self.expires_at

    @staticmethod
    def hash_value(value):
        return hashlib.sha256(value.encode()).hexdigest()
