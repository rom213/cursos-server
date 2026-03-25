from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SystemVariable(Base):
    __tablename__ = "system_variables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dato: Mapped[str] = mapped_column(String(255), nullable=False)
    observacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    tabla: Mapped[str | None] = mapped_column(String(100), nullable=True)
    campo_codigo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    def __init__(self, campo_codigo, dato, descripcion=None, observacion=None, tabla=None):
        self.campo_codigo = campo_codigo
        self.dato = dato
        self.descripcion = descripcion
        self.observacion = observacion
        self.tabla = tabla

    def to_dict(self):
        return {
            "id": self.id,
            "campo_codigo": self.campo_codigo,
            "dato": self.dato,
            "descripcion": self.descripcion,
            "observacion": self.observacion,
            "tabla": self.tabla,
        }
