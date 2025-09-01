
from abc import ABC, abstractmethod
from typing import List
from models.Refer import Refer
from models.Refund import Refund
from models.Payment import Payment
from models.Category import Category





class ReferQueryService:
    @classmethod
    def get_by_user_and_date(cls, google_id, date_init, date_end) -> List[Refer]:
        """trae los reembolsos desde refer segun el atributo google_id, refund segun la fecha de reembolso"""
        return Refer.query.join(Refund, Refund.id == Refer.refund_id) \
             .join(Payment, Payment.id== Refer.payment_id)\
             .join(Category, Category.id == Payment.category_id)\
            .filter(Refer.google_id == google_id) \
            .filter(Refund.created_at >= date_init) \
            .filter(Refund.created_at <= date_end) \
            .all()
