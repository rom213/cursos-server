import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


category_relations = Table(
    "category_relations",
    Base.metadata,
    Column("category_id", Integer, ForeignKey("category.id"), primary_key=True),
    Column("related_category_id", Integer, ForeignKey("category.id"), primary_key=True),
)


class TipoCategoria(enum.Enum):
    CAT_1 = 1
    CAT_2 = 2
    CAT_3 = 3
    CAT_4 = 4


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_categoria: Mapped[TipoCategoria | None] = mapped_column(SAEnum(TipoCategoria), nullable=True)
    titulo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frase_1: Mapped[str | None] = mapped_column(String(200), nullable=True)
    frase_2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    imagen_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    num_per: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contenido: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    pregunta_respuesta: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    seccion_plataformas: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    seccion_temas: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    seccion_lista_completa: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    descuento: Mapped[str] = mapped_column(String(20), default="0", nullable=False)
    precio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duracion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    delete_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    courses = relationship("Course", backref="category", lazy=True)

    related_categories = relationship(
        "Category",
        secondary=category_relations,
        primaryjoin=lambda: Category.id == category_relations.c.category_id,
        secondaryjoin=lambda: Category.id == category_relations.c.related_category_id,
        lazy="select",
    )
