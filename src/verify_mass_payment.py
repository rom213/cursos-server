from app import app, db
from models.User import User
from models.Refer import Refer
from models.Refund import Refund
from models.account import AccountType
from servises.refund.mass_payment_service import MassPaymentService
from datetime import datetime, timedelta
import uuid

def verify():
    with app.app_context():
        # 1. Create dummy user
        google_id = f"test_user_{uuid.uuid4()}"
        email = f"test_{uuid.uuid4()}@example.com"
        user = User(google_id=google_id, name="Test User", email=email, picture="avatar.jpg")
        db.session.add(user)
        db.session.commit() # Commit user first to satisfy FK
        
        # 2. Create dummy refers
        refer1 = Refer(google_id=google_id, porcentage="10", value="100.0", is_pay=False)
        refer2 = Refer(google_id=google_id, porcentage="10", value="50.0", is_pay=False)
        db.session.add(refer1)
        db.session.add(refer2)
        db.session.commit()
        
        print(f"Created user {google_id} and 2 refers (100.0, 50.0)")
        
        # 3. Prepare refund data
        refund_data = {
            "type_acc_em": AccountType.nequi, # Assuming NEQUI exists in AccountType enum
            "type_acc_re": AccountType.nequi,
            "titular_acc_em": "Test Sender",
            "titular_acc_res": "Test Receiver",
            "number_acc_em": "123456789",
            "code_reference": "REF123",
            "image": "path/to/image.jpg"
        }
        
        # 4. Call Service
        date_init = datetime.utcnow() - timedelta(days=1)
        date_end = datetime.utcnow() + timedelta(days=1)
        
        print("Calling MassPaymentService...")
        result = MassPaymentService.process_mass_payment(
            google_id=google_id,
            date_init=date_init,
            date_end=date_end,
            refund_data=refund_data
        )
        
        print("Result:", result)
        
        # 5. Verify
        if result["status"] == "success":
            refund_id = result["refund_id"]
            refund = Refund.query.get(refund_id)
            print(f"Refund created: ID={refund.id}, Value={refund.value}")
            
            # Check refers
            r1 = Refer.query.get(refer1.id)
            r2 = Refer.query.get(refer2.id)
            
            print(f"Refer 1: RefundID={r1.refund_id}, IsPay={r1.is_pay}")
            print(f"Refer 2: RefundID={r2.refund_id}, IsPay={r2.is_pay}")
            
            if r1.refund_id == refund.id and r2.refund_id == refund.id and float(refund.value) == 150.0:
                print("VERIFICATION SUCCESSFUL")
            else:
                print("VERIFICATION FAILED: Data mismatch")
        else:
            print("VERIFICATION FAILED: Service returned error")

if __name__ == "__main__":
    verify()
