from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class TiendaCourse(Base):
    __tablename__ = "tienda_course"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str | None] = mapped_column(String(255))
    autor: Mapped[str | None] = mapped_column(String(255))
    url_curso: Mapped[str | None] = mapped_column(String(500))
    pack_id: Mapped[str | None] = mapped_column(String(100))
    pack_nombre: Mapped[str | None] = mapped_column(String(255))
    pack_cantidad_cursos: Mapped[int | None] = mapped_column(Integer)
    pilar_id: Mapped[str | None] = mapped_column(String(100))
    keywords: Mapped[str | None] = mapped_column(Text)

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "autor": self.autor,
            "url_curso": self.url_curso,
            "pack_id": self.pack_id,
            "pack_nombre": self.pack_nombre,
            "pack_cantidad_cursos": self.pack_cantidad_cursos,
            "pilar_id": self.pilar_id,
            "keywords": self.keywords,
        }
