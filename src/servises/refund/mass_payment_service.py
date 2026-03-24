from models import db
from models.Refer import Refer
from models.Refund import Refund
from models.account import AccountType
from datetime import datetime
from typing import List, Dict, Any, Union
import json

class MassPaymentService:
    @staticmethod
    def process_mass_payment(google_id: str, refund_data: Dict[str, Any], list_ids_refers: Union[List[str], str]) -> Dict[str, Any]:
        """ 
        Processes a mass payment for a referrer within a date range.
        Aggregates multiple Refer records into a single Refund.
        """
        if isinstance(list_ids_refers, str):
            try:
                list_ids_refers = json.loads(list_ids_refers)
            except json.JSONDecodeError:
                return {"status": "error", "message": "Invalid format for list_ids_refers"}
        
        # 1. Find unpaid refers
        refers = Refer.query.filter(
            Refer.google_id == google_id,
            Refer.refund_id == None,
            Refer.id.in_(list_ids_refers)
        ).all()

        if not refers:
            return {"status": "error", "message": "No unpaid referrals found for this user in the given date range."}

        # 2. Calculate total value
        total_value = 0.0
        for refer in refers:
            try:
                total_value += float(refer.value)
            except ValueError:
                # Handle cases where value might not be a valid float
                pass
        
        # 3. Create Refund
        # Ensure refund_data contains necessary fields
        try:
            new_refund = Refund(
                type_acc_em=refund_data.get("type_acc_em"),
                titular_acc_em=refund_data.get("titular_acc_em"),
                number_acc_em=refund_data.get("number_acc_em"),   
                type_acc_re=refund_data.get("type_acc_re"),
                titular_acc_res=refund_data.get("titular_acc_res"),
                number_acc_res=refund_data.get("number_acc_res"),
                value=str(total_value), # Store total as string to match model
                image=refund_data.get("image"),
                code_reference=refund_data.get("code_reference"),
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_refund)
            db.session.flush() # Flush to get the ID
            
            # 4. Update Refers
            for refer in refers:
                refer.refund_id = new_refund.id
                refer.is_pay = True
                db.session.add(refer)
            
            db.session.commit()
            
            return {
                "status": "success", 
                "message": "Mass payment processed successfully.",
                "refund_id": new_refund.id,
                "total_value": total_value,
                "refers_count": len(refers)
            }
            
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": str(e)}
