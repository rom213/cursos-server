from flask import Blueprint, request, jsonify
import hashlib



payments_bp = Blueprint("payments", __name__)



API_KEY = "WTwXvH9RHxXSOaap990f76ti6o" 


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

        print(request.form.to_dict())
        
        if not all([merchant_id, reference_sale, value, currency, state_pol, received_sign]):
            return jsonify({"error": "Missing parameters"}), 400
        
        value = float(value)
        formatted_value = f"{value:.1f}" if value % 1 == 0 else f"{value:.2f}"
        
        signature_string = f"{API_KEY}~{merchant_id}~{reference_sale}~{formatted_value}~{currency}~{state_pol}"
        generated_sign = hashlib.md5(signature_string.encode()).hexdigest()
        
        # Verificar la firma
        if received_sign != generated_sign:
            return jsonify({"error": "Invalid signature"}), 403
        
        # Aquí puedes procesar la transacción en tu base de datos
        # Ejemplo: actualizar órdenes, inventarios, etc.

        #VERIFICAMOS QUE EXISTA LA TRANSACCION NO EXISTA EN LA BASE DE DATOS DE LO CONTRARIO HAY VIOLACION AL SISTEMA
        transaction_status = "approved" if state_pol == "4" else "rejected"

        
        
        return jsonify({"message": "Confirmation received", "transaction_status": transaction_status}), 200
    except:
        print("hola hubo un error")
        return jsonify({"message": "Confirmation received", "transaction_status": "error"}), 200

