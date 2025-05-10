from flask import Blueprint, request, jsonify, session
from servises.groups.repository import GroupRepository
from servises.payment.payment_repository import PaymentRespository
from servises.categories.category_model import CategoryModel
from servises.Users.user_model import UserModel
import hashlib
import os
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


payments_bp = Blueprint("payments", __name__)





def parse_data(dat, reference_sale):
    items = dat.strip('|').split('|')  # Eliminar '|' inicial y final, luego dividir por '|'
    parsed_items = []

    for item in items:
        parts = item.split(',')
        obj = {
            "category_id": int(parts[0]),  # Convertir el primer valor a entero
            "google_id": parts[1] if len(parts) > 1 else None,  # Verificar si hay datos
            "google_id_refer": parts[2] if len(parts) > 2 else None,
            "reference_code": reference_sale
        }
        parsed_items.append(obj)

    return parsed_items



@payments_bp.route("/payu-confirmation", methods=["POST"])
def payu_confirmation():
    try:
        data = request.form.to_dict()
        
        # Extraer los parámetros necesarios para la firma
        merchant_id = data.get("merchant_id")
        reference_sale = data.get("reference_sale")
        value = data.get("value")
        currency = data.get("currency")
        state_pol = data.get("state_pol")
        received_sign = data.get("sign")


        #print(request.form.to_dict())
        
        if not all([merchant_id, reference_sale, value, currency, state_pol, received_sign]):
            return jsonify({"error": "Missing parameters"}), 400
        
        # value = float(value)
        # formatted_value = f"{value:.1f}" if value % 1 == 0 else f"{value:.2f}"
        
        # signature_string = f"{os.getenv("PAYU_API_KEY")}~{merchant_id}~{reference_sale}~{formatted_value}~{currency}~{state_pol}"
        # generated_sign = hashlib.md5(signature_string.encode()).hexdigest()
        
        # # Verificar la firma
        # if received_sign != generated_sign:
        #     return jsonify({"error": "Invalid signature"}), 403


        
        # Aquí puedes procesar la transacción en tu base de datos
        # Ejemplo: actualizar órdenes, inventarios, etc.

        #VERIFICAMOS QUE EXISTA LA TRANSACCION NO EXISTA EN LA BASE DE DATOS DE LO CONTRARIO HAY VIOLACION AL SISTEMA los datos que son google_id y 
        # y category seran
        #enviados concatenanos con reference sale;  
        transaction_status = "approved" if state_pol == "4" else "rejected"

        # Campos extra a procesar
        extra_fields = ["extra1", "extra2", "extra3", "extra4"]

        # Parseamos todos los extras de una sola vez
        cart_data_list = []
        for field in extra_fields:
            raw_value = data.get(field)
            if raw_value:  # si viene None o cadena vacía, lo ignora
                cart_data_list.append(parse_data(raw_value, reference_sale))

                
        # Si está aprobada, procesamos cada lista
        if state_pol == "4":
            for cart_data in cart_data_list:
                if isinstance(cart_data, list):
                    for item in cart_data:
                        try:
                            GroupRepository.process_member_addition(
                                "agregar_miembro_grupo",
                                data=item
                            )
                        except Exception as e:
                            # Loguea cualquier error sin romper el flujo
                            logger.error(f"Error procesando {item}: {e}")

        return jsonify({
            "message": "Confirmation received",
            "transaction_status": transaction_status
        }), 200
    except:
        print("hola hubo un error")
        return jsonify({"message": "Confirmation received", "transaction_status": "error"}), 200



@payments_bp.route("/payu-firm", methods=["POST"])
def payu_signature():
        try:
            if "user" not in session:
                return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401
            

            data= request.get_json()
            if not data or "categories" not in data:
                return jsonify({"error": "Invalid payload"}), 400
            
            categories = data["categories"] 
            is_first_bought = not UserModel.is_bought(google_id=session["user"]["google_id"])

            price = 0
            for category in categories:
                id_category = category.get("id_category")
                cat = CategoryModel.get_by_id(category_id=id_category)
                cat.calc_price(is_middle_price=is_first_bought)
                price = price + cat.descuento_total_price
                if is_first_bought is True:
                    is_first_bought= False
            

            firm= PaymentRespository(price=price)
            firm.generate_firm()

            return jsonify({"signature": firm.signature, "reference_code":firm.reference_code, "price": firm.price }), 200
        except :
            return jsonify({"message": "posible error verificar"}), 500
