from models import db
from models.PaymentResgister import PaymentRegister

class PaymentRegisterRepository:
    @staticmethod
    def create_pending(items, ref_code):
        """
        Creates and saves multiple pending PaymentRegister entries from item data.
        """
        for item in items:
            pr = PaymentRegister(
                pay_value_refer=str(item["pay_value_refer"]),
                google_id=item["google_id"],
                google_id_refer=item["google_id_refer"],
                category_id=item["category_id"],
                currency=item["moneda"],
                codeValue=ref_code,
                status='pending'
            )
            db.session.add(pr)
        db.session.commit()
    
    @classmethod
    def getItemsPayment(cls, payment_resgistro_id):
        registros=PaymentRegister.query.filter(PaymentRegister.codeValue==payment_resgistro_id).all()
        return registros

        