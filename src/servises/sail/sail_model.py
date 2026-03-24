
from abc import ABC, abstractmethod
from typing import List
from models.Refer import Refer
from models.Refund import Refund
from models.Payment import Payment
from models.Category import Category





from sqlalchemy import and_  # <--- Importa esto

class ReferQueryService:
    @classmethod
    def get_by_user_and_date(cls, google_id, date_init, date_end) -> List[Refer]:
        """
        Trae los 'Refer' de un usuario. Si tiene un reembolso (Refund)
        dentro del rango de fechas, lo incluye. Si no tiene reembolso,
        o el reembolso está fuera de fecha, igual trae el 'Refer'
        pero el 'Refund' asociado será NULL.
        """
        refund_join_condition = and_(
            Refund.id == Refer.refund_id,
            Refund.created_at >= date_init,
            Refund.created_at <= date_end
        )

        return Refer.query.join(
            Refund, 
            refund_join_condition, 
            isouter=True
        ).join(
            Payment, Payment.id == Refer.payment_id
        ).join(
            Category, Category.id == Payment.category_id
        ).filter(
            Refer.google_id == google_id
        ).all()