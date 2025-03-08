import os
import hashlib
import uuid
from dotenv import load_dotenv

load_dotenv()

class PaymentRespository():
    
    def __init__(self, price, PAYU_API_KEY = os.getenv("PAYU_API_KEY"), PAYU_MERCHANT_ID = os.getenv("PAYU_MERCHANT_ID")):
        self.PAYU_API_KEY = PAYU_API_KEY
        self.PAYU_MERCHANT_ID = PAYU_MERCHANT_ID
        self.signature= ""
        self.price= price
        self.reference_code= ""

    def generate_firm(self):
        self.reference_code = str(uuid.uuid4()) 
        signature_string = f"{self.PAYU_API_KEY}~{self.PAYU_MERCHANT_ID}~{self.reference_code}~{self.price}~COP"
        self.signature = hashlib.md5(signature_string.encode()).hexdigest()
