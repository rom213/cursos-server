import os
import uuid
from abc import ABC, abstractmethod
from typing import List
from PIL import Image, UnidentifiedImageError
from models import db
from models.Refer import Refer
from models.User import User
from models.Refund import Refund
from models.Payment import Payment
from datetime import datetime
from sqlalchemy import or_, func
from typing import List, Dict, Any


# -------------------------------
# SRP: Consulta especializada
# -------------------------------
class RefundQueryService:
    @classmethod
    def get_by_user_and_date(cls, google_id, date_init, date_end) -> List[Refer]:
        """trae los reembolsos desde refer segun el atributo google_id, refund segun la fecha de reembolso"""
        return Refer.query.join(Refund, Refund.id == Refer.refund_id) \
             .join(Payment, Payment.id== Refer.payment_id)\
            .filter(Refer.google_id == google_id) \
            .filter(Refund.created_at >= date_init) \
            .filter(Refund.created_at <= date_end) \
            .all()
            
    @classmethod
    def search_refunds(cls, date_init: datetime, date_end: datetime, search_term: str = None, 
                      page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Busca reembolsos por fecha y término de búsqueda con paginación
        
        Args:
            date_init: Fecha de inicio
            date_end: Fecha de fin
            search_term: Término de búsqueda (opcional)
            page: Número de página
            per_page: Elementos por página
            
        Returns:
            Dict con records, total, pages, current_page, per_page
        """
        query = Refund.query \
            .join(Refer, Refer.refund_id == Refund.id) \
            .join(Payment, Payment.id == Refer.payment_id) \
            .join(User, User.google_id == Refer.google_id) \
            .filter(Refund.created_at >= date_init) \
            .filter(Refund.created_at <= date_end)
        
        # Aplicar búsqueda si existe término
        if search_term and search_term.strip():
            search_pattern = f"%{search_term.strip()}%"
            query = query.filter(
                or_(
                    Refer.google_id.ilike(search_pattern),
                    User.name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    func.cast(Refund.value, db.String).ilike(search_pattern),
                    func.cast(Refer.value, db.String).ilike(search_pattern)
                )
            )
        
        # Ordenar por fecha descendente (más recientes primero)
        query = query.distinct().order_by(Refund.created_at.desc())
        
        # Aplicar paginación
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            "records": pagination.items,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
        
    @classmethod
    def get_refund_date(cls, date_init, date_end)-> List[Refer]:
        """trae los reembolsos desde refer  segun la fecha de reembolso"""
        return Refer.query.join(Refund, Refund.id == Refer.refund_id) \
             .join(Payment, Payment.id== Refer.payment_id)\
            .filter(Refund.created_at >= date_init) \
            .filter(Refund.created_at <= date_end) \
            .all()
            
            
    @classmethod      
    def get_refunds_by_google_id(cls, google_id, date_init, date_end) -> List[Refer]:
        return Refer.query.join(Refund, Refund.id == Refer.refund_id) \
            .join(Payment, Payment.id == Refer.payment_id) \
            .filter(Refer.google_id == google_id) \
            .filter(Refer.created_at >= date_init) \
            .filter(Refer.created_at <= date_end) \
            .all()
            
    @classmethod      
    def get_refund_by_id(cls, refund_id) -> List[Refer]:
        return Refer.query.join(Refund, Refund.id == Refer.refund_id) \
            .join(Payment, Payment.id == Refer.payment_id) \
            .filter(Refund.id== refund_id) \
            .all()


class IRefundRepository(ABC):
    @abstractmethod
    def save(self, refund: Refund):
        pass


class RefundRepository(IRefundRepository):
    def save(self, refund: Refund):
        db.session.add(refund)
        db.session.commit()


class RefundCreator:
    def __init__(self, repository: IRefundRepository):
        self.repository = repository

    def create_refund(self, refund_data: dict):
        refund = Refund(**refund_data)
        self.repository.save(refund)
        return refund


class IImageValidator(ABC):
    @abstractmethod
    def is_valid(self, image_input) -> bool:
        pass


class PILImageValidator(IImageValidator):
    def is_valid(self, image_input) -> bool:
        if isinstance(image_input, Image.Image):
            return True
        try:
            if hasattr(image_input, 'read'):
                pos = image_input.tell() if hasattr(image_input, 'tell') else None
                image = Image.open(image_input)
                image.verify()
                image_input.seek(pos or 0)
                return True
        except (UnidentifiedImageError, AttributeError, ValueError, OSError):
            return False
        return False


class ImageStorageService:
    def __init__(self, image_input, validator: IImageValidator):
        self._img = image_input
        self._validator = validator
        self._path = None

        if not self._validator.is_valid(self._img):
            raise ValueError("El archivo proporcionado no es una imagen válida.")

    def save(self) -> str:
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        unique_filename = f"{uuid.uuid4()}.jpg"
        file_path = os.path.join(upload_dir, unique_filename)

        if isinstance(self._img, Image.Image):
            img_to_save = self._img.convert('RGB') if self._img.mode == 'RGBA' else self._img
            img_to_save.save(file_path, "JPEG")
        else:
            img_data = Image.open(self._img)
            img_data = img_data.convert('RGB') if img_data.mode == 'RGBA' else img_data
            img_data.save(file_path, "JPEG")

        self._path = file_path
        return file_path

    def get_path(self) -> str:
        if not self._path:
            raise ValueError("La imagen aún no ha sido guardada.")
        return self._path
