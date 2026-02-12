from flask import Blueprint, request, jsonify, session
from servises.groups.repository import GroupRepository
from servises.payment.payment_repository import PaymentRespository
from servises.categories.category_model import CategoryModel
from servises.Users.user_model import UserModel
import paypalrestsdk
from models import db
from models.PaymentResgister import PaymentRegister
from servises.payment_register.payment_register_repository import PaymentRegisterRepository
import uuid
import hashlib
import os
import logging



paypalrestsdk.configure({
    "mode": "sandbox",  # Pon "live para pagos reales" y "sandbox para pruebas"
    "client_id": "Aew9PIGagtvhZ6jRQc83QvG5_c7HwBiDH80DMHJuYIl5py8i9U94o_VeayP1H26zvO6V3rfKK-GqyS4b",  # Reemplaza con tu Client ID
    "client_secret": "EOBT3PiVBjI3pSUDXKnn01b3FlGsjtLlnrHzoTvtnx21Pygm4cVUBgcsjjLtI6wCYh3Rc4Uc_6cli7l-"  # Reemplaza con tu Client Secret
})


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


payments_bp = Blueprint("payments", __name__)





def parse_data(dat, reference_sale, pay_value):
    items = dat.strip('|').split('|')  # Eliminar '|' inicial y final, luego dividir por '|'
    parsed_items = []

    for item in items:
        parts = item.split(',')
        obj = {
            "category_id": int(parts[0]),  # Convertir el primer valor a entero
            "google_id": parts[1] if len(parts) > 1 else None,  # Verificar si hay datos
            "google_id_refer": parts[2] if len(parts) > 2 else None,
            "reference_code": reference_sale,
            "pay_value_refer":pay_value
        }
        parsed_items.append(obj)

    return parsed_items


def calculate_total_price_and_items(categories, google_id="118070327157829661695"):
    """
    Calculates total price, payment items, and PayPal items in a single loop,
    applying sequential discounts: first category full (if first buy), others 50% off.
    """
    total_price = 0
    payment_items = []
    paypal_items = []
    is_first_bought =  not UserModel.is_bought(google_id=session["user"]["google_id"])

    for category in categories:
        id_category = category.get("id_category")
        google_id_refer = category.get("google_id_refer", None)
        cat = CategoryModel.get_by_id(category_id=id_category)
        values = cat.calc_price(is_middle_price=True, is_not_payu_request=False)
        price = values.get("precio_final")
        if is_first_bought:
            is_first_bought = False
        total_price += price

        # For PaymentRegister items
        payment_items.append({
            "category_id": id_category,
            "google_id": google_id,
            "google_id_refer": google_id_refer,
            "pay_value_refer": price,
            "moneda": "USD"
        })

        # For PayPal items
        paypal_items.append({
            "name": getattr(cat, 'titulo', f"Category {id_category}"),  # Use 'titulo' from model
            "sku": f"cat_{id_category}",
            "price": f"{price:.2f}",
            "currency": "USD",
            "quantity": 1
        })

    return total_price, payment_items, paypal_items


def calculate_total_price_and_items_cupon(categories, google_id="118070327157829661695"):
    """
    Calculates total price, payment items, and PayPal items in a single loop,
    applying sequential discounts: first category full (if first buy), others 50% off.
    """
    total_price = 0
    payment_items = []
    paypal_items = []
    is_first_bought =  not UserModel.is_bought(google_id=session["user"]["google_id"])

    for category in categories:
        id_category = category.get("id_category")
        google_id_refer = category.get("google_id_refer", None)
        cat = CategoryModel.get_by_id(category_id=id_category)
        values = cat.calc_price(is_middle_price=True, is_not_payu_request=False)
        price = values.get("precio_final")
        if is_first_bought:
            price = price - 10000
            is_first_bought = False
        total_price += price

        # For PaymentRegister items
        payment_items.append({
            "category_id": id_category,
            "google_id": google_id,
            "google_id_refer": google_id_refer,
            "pay_value_refer": price,
            "moneda": "USD"
        })

        # For PayPal items
        paypal_items.append({
            "name": getattr(cat, 'titulo', f"Category {id_category}"),  # Use 'titulo' from model
            "sku": f"cat_{id_category}",
            "price": f"{price:.2f}",
            "currency": "USD",
            "quantity": 1
        })

    return total_price, payment_items, paypal_items


def calculate_total_price(categories):
    """
    Calculates total price only, applying sequential discounts.
    """
    total_price = 0
    for category in categories:
        id_category = category.get("id_category")
        cat = CategoryModel.get_by_id(category_id=id_category)
        values = cat.calc_price(is_middle_price=True, is_not_payu_request=False)
        price = values.get("precio_final")
        total_price += price

    return total_price

def validarSeccionUsuario():
    if "user" not in session:
        return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401
    return None


def registrarPagoPagado(registros):
    for item in registros:
        item.cambiarStatus()
     



def generarObjetoParaGuardarLosRegistroDePago(registros, payment_id):
    items=[]
    for item in registros:
        obj = {
            "category_id": int(item.category_id),  # Convertir el primer valor a entero
            "google_id": item.google_id,  # Verificar si hay datos
            "google_id_refer": item.google_id_refer,
            "reference_code": payment_id,
            "pay_value_refer":item.pay_value_refer
        }
        items.append(obj)
    return items
    


def revisarYGuardarInformacionDePago(registros):
    for item in registros:
        try:
            GroupRepository.process_member_addition(
                "agregar_miembro_grupo",
                     data=item
                    )
        except Exception as e:
         # Loguea cualquier error sin romper el flujo
            logger.error(f"Error procesando {item}: {e}")

def calculate_total_price_cupon(categories, porcentaje_descuento):
    """
    Calculates total price only, applying sequential discounts.
    """
    total_price = 0
    # Asegúrate de que session y UserModel estén disponibles en este scope
     
    for category in categories:
        id_category = category.get("id_category")
        cat = CategoryModel.get_by_id(category_id=id_category)
        values = cat.calc_price(is_middle_price=True, is_not_payu_request=False)
        price = values.get("precio_final")
        total_price += price
    
    descuento_valor = total_price * (porcentaje_descuento / 100)
    total_price = total_price - descuento_valor
    
    return total_price, descuento_valor


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

        cart_data_list = []
        for field in extra_fields:
            raw_value = data.get(field)
            if raw_value:  # si viene None o cadena vacía, lo ignora
                cart_data_list.append(parse_data(raw_value, reference_sale, value))

        print(cart_data_list)

        # Si está aprobada, procesamos cada lista
        if state_pol == "4":
            for cart_data in cart_data_list:
                if isinstance(cart_data, list):
                    revisarYGuardarInformacionDePago(cart_data)

        return jsonify({
            "message": "Confirmation received",
            "transaction_status": transaction_status
        }), 200
    except:
        print("hola hubo un error")
        return jsonify({"message": "Confirmation received", "transaction_status": "error"}), 200


@payments_bp.route("/paypal/webhook", methods=["POST"])
def paypal_webhook():
    try:
        data = request.json
        event_type = data.get("event_type")
        if event_type == "PAYMENTS.PAYMENT.CREATED":
            resource = data.get("resource", {})
            payment_id = resource.get("id")
            payer_id = resource.get("payer", {}).get("payer_info", {}).get("payer_id")
            
            
            registerPayment=[]
            for item in resource["transactions"]:
                registerCode=item.get('description')
                registerPayment= PaymentRegisterRepository.getItemsPayment(registerCode)
             
            registrosParceados= generarObjetoParaGuardarLosRegistroDePago(registerPayment, payment_id)

            #esto es cuado se guar en la bd ahorita esta aca por pruebas 
            revisarYGuardarInformacionDePago(registrosParceados)
            registrarPagoPagado(registerPayment)
            
            
            
            payment = paypalrestsdk.Payment.find(payment_id)

            if payment.execute({"payer_id": payer_id}):
                print("se guardara en la bd")
                return jsonify({"status": "captured", "payment": payment.to_dict()}), 200
            else:
                return jsonify({"status": "error", "details": payment.error}), 400

        if event_type == "PAYMENT.SALE.REFUNDED":
            refund_id = resource.get("id")
            parent_payment = resource.get("parent_payment")
            amount = resource.get("amount", {})

            # Aquí actualizas tu BD:
            # - Buscar el pago original (con parent_payment)
            # - Marcarlo como reembolsado
            # - Guardar el monto y refund_id
            return jsonify({
                "status": "refund_received",
                "refund_id": refund_id,
                "parent_payment": parent_payment,
                "amount": amount
            }), 200

        if event_type == "PAYMENT.SALE.REVERSED":

            return jsonify({
                "status": "reversed",
                "resource": resource
            }), 200


        return jsonify({"status": "ignored", "event": event_type}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



















@payments_bp.route("/payu-firm", methods=["POST"])
def payu_signature():
        try:
            isLoggin= validarSeccionUsuario()
            if isLoggin:
                return  isLoggin

            categories = request.get_json()["categories"]
            precio = calculate_total_price(categories)

            firm= PaymentRespository(price=precio)
            firm.generate_firm()

            return jsonify({"signature": firm.signature, "reference_code":firm.reference_code, "price": firm.price }), 200
        except :
            return jsonify({"message": "posible error verificar"}), 500

@payments_bp.route("/payu-firm-cupon", methods=["POST"])
def payu_signature_cupon():
        try:
            isLoggin= validarSeccionUsuario()
            if isLoggin:
                return  isLoggin

            categories = request.get_json()["categories"]
            cupon = request.get_json()["cupon"]


            user=UserModel.validar_cupon(cupon)

            if not user:
                return jsonify({"message": "No tienes cupon"}), 400

            precio, descuento_aplicado = calculate_total_price_cupon(categories, user.descuento_referido)
            firm= PaymentRespository(price=precio)
            firm.generate_firm()
            return jsonify({
                "status": "success",
                "message": "OK",
                "records": [{
                    "signature": firm.signature, 
                    "reference_code":firm.reference_code, 
                    "price": firm.price, 
                    "google_id":user.google_id,
                    "descuento":descuento_aplicado
                }]
            }), 200
        except Exception as e:
            print(e)
            return jsonify({"message": "posible error verificar"}), 500


    

@payments_bp.route("/paypal/return", methods=["POST", "GET"])
def paypal_return():
    try:
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("Error procesando webhook:", e)
        return jsonify({"error": "Webhook error"}), 500



@payments_bp.route("/paypal-generate-link-pay", methods=["POST"])
def paypal_generate_link_pay():
    try:
        # Validar sesión si es necesario
        # isLoggin = validarSeccionUsuario()
        # if isLoggin: return isLoggin

        data = request.get_json()
        categories = data["categories"]

        precio, items, paypal_items = calculate_total_price_and_items(categories, google_id=session["user"]["google_id"])

        ref_code = str(uuid.uuid4())[:20]
        PaymentRegisterRepository.create_pending(items, ref_code)
        
        
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": f"http://localhost:5002/paypal/return?ref={ref_code}",  # URL de retorno (cuando el pago es aprobado)
                "cancel_url": "http://localhost:5002/paypal/cancel"   # URL de cancelación
            },
            "transactions": [{
                "item_list": {
                    "items": paypal_items
                },
                "amount": {
                    "total": f"{precio:.2f}",
                    "currency": "USD"
                },
                "description": f"{ref_code}"
            }]
        })

        
        if payment.create():
            # Buscar el link de aprobación
            for link in payment.links:
                if link.method == "REDIRECT":
                    return jsonify({"approval_url": link.href}), 200
            return jsonify({"message": "No se encontró link de aprobación"}), 500
        else:
            return jsonify({"error": payment.error}), 400

    except Exception as e:
        print("Error PayPal:", e)
        return jsonify({"message": "error"}), 500



