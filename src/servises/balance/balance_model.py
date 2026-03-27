from models.Refer import Refer
from models.Payment import Payment
from sqlalchemy import and_
from dataclasses import dataclass
from datetime import datetime




class BalanceModel:
    @classmethod
    def get_all_sales_by_me(
        cls, 
        google_id: str, 
        date_init: datetime, 
        date_end: datetime
    ) :

        # Obtengo todos los registros para ese usuario y rango de fechas
        refers = (
            Refer.query.join(Payment, Payment.id == Refer.payment_id)
            .filter(
                Refer.google_id == google_id,
                Refer.created_at >= date_init,
                Refer.created_at <= date_end
            )
            .all()
        )

        # Inicializo los contadores
        courses_sells_count = 0
        courses_value_sells = 0
        courses_value_sells_refunds = 0
        courses_value_sells_not_refunds = 0
        courses_payments_value=0
        list_ids_refers=[]

        # Recorro y voy acumulando
        for item in refers:
            value = int(item.value or 0)  # aseguro que sea entero
            courses_sells_count += 1
            courses_value_sells += value
            courses_payments_value+=int(item.payment.price)

            if item.refund_id is not None:
                courses_value_sells_refunds += value
            else:
                courses_value_sells_not_refunds += value
            list_ids_refers.append(item.id);

        # Devuelvo el objeto con todos los datos
        return  {
            "counts":courses_sells_count,
            "total_value":courses_value_sells,
            "refunded_value":courses_value_sells_refunds,
            "non_refunded_value":courses_value_sells_not_refunds,
            "courses_payments_value":courses_payments_value,
            "list_ids_refers":list_ids_refers
            }
        
    @classmethod
    def get_all_sales(
        cls, 
        date_init: datetime, 
        date_end: datetime
    ) :

        # Obtengo todos los registros para ese usuario y rango de fechas
        refers = (
            Refer.query.join(Payment, Payment.id == Refer.payment_id)
            .filter(
                Refer.created_at >= date_init,
                Refer.created_at <= date_end
            )
            .all()
        )

        # Inicializo los contadores
        courses_sells_count = 0
        courses_value_sells = 0
        courses_value_sells_refunds = 0
        courses_value_sells_not_refunds = 0
        courses_payments_value=0

        # Recorro y voy acumulando
        for item in refers:
            value = int(item.value or 0)  # aseguro que sea entero
            courses_sells_count += 1
            courses_value_sells += value
            courses_payments_value+=int(item.payment.price)

            if item.refund_id is not None:
                courses_value_sells_refunds += value
            else:
                courses_value_sells_not_refunds += value

        # Devuelvo el objeto con todos los datos
        return  {
            "counts":courses_sells_count,
            "total_value":courses_value_sells,
            "refunded_value":courses_value_sells_refunds,
            "non_refunded_value":courses_value_sells_not_refunds,
            "courses_payments_value":courses_payments_value
            }
        

