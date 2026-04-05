import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class TipoUsuario(enum.Enum):
    NUEVO = "nuevo"
    VENDEDOR = "vendedor"
    CUPON = "cupon"
    TERCERO = "tercero"


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    rol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    picture: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    num_whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vista_previa_drive: Mapped[bool] = mapped_column(Integer, default=1)
    delete_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    codigo_referido: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    descuento_referido: Mapped[float] = mapped_column(Float, default=0.0)
    tipo_usuario: Mapped[TipoUsuario | None] = mapped_column(
        SAEnum(TipoUsuario), default=TipoUsuario.NUEVO, nullable=True
    )

    accounts = relationship("Account", backref="user", lazy=True)

    def __init__(
        self,
        google_id: str,
        email: str,
        name: str,
        picture: str,
        rol: str = "user",
        country: str | None = None,
    ):
        self.google_id = google_id
        self.email = email
        self.rol = rol
        self.name = name
        self.picture = picture
        self.country = country

    def to_dict(self):
        return {
            "id": self.id,
            "google_id": self.google_id,
            "codigo_referido": self.codigo_referido,
            "email": self.email,
            "country": self.country,
            "num_whatsapp": self.num_whatsapp,
            "rol": self.rol,
            "name": self.name,
            "picture": self.picture,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "delete_at": self.delete_at.isoformat() if self.delete_at else None,
        }
