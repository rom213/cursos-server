from flask import Blueprint, request, jsonify, session, current_app
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
from models.User import TipoUsuario
from models.Category import TipoCategoria
from models.SystemVariable import SystemVariable
from utils.async_executor import executor
import asyncio
import requests

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



def calculate_total_price_and_items(categories, google_id="118070327157829661695", google_id_refer=None,porcentaje_descuento=0):
    """
    Calculates total price, payment items, and PayPal items in a single loop,
    applying sequential discounts: first category full (if first buy), others 50% off.
    """
    total_price = 0
    payment_items = []
    paypal_items = []

    for category in categories:
        id_category = category.get("id_category")
        cat = CategoryModel.get_by_id(category_id=id_category)
        values = cat.calc_price(descuento=porcentaje_descuento)
        price = values.get("precio_final")
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

def verificarYActualizarVendedor(registros):
    """
    Verifica si en los registros de pago hay compras de categorías CAT_1 o CAT_2.
    Si es así, actualiza al usuario correspondiente a TipoUsuario.VENDEDOR.
    """
    try:
        target_categories = [TipoCategoria.CAT_1, TipoCategoria.CAT_2]

        for item in registros:
            category_id = item.get('category_id')
            google_id = item.get('google_id')

            if not category_id or not google_id:
                continue

            category = CategoryModel.get_by_id(category_id)
            if not category:
                continue

            # Solo CAT_1 y CAT_2 otorgan rango de VENDEDOR
            if category.tipo_categoria in target_categories:
                user = UserModel.get_by_google_id(google_id)
                if user and user.tipo_usuario != TipoUsuario.VENDEDOR:
                    logger.info(f"Actualizando usuario {google_id} a VENDEDOR por compra de categoria {category_id}")
                    user.update(tipo_usuario=TipoUsuario.VENDEDOR)

    except Exception as e:
        logger.error(f"Error al verificar/actualizar vendedor: {e}")


def calculate_total_price(categories, porcentaje_descuento=0):
    """
    Calculates total price only, applying sequential discounts.
    """
    total_price = 0
    # Asegúrate de que session y UserModel estén disponibles en este scope
     
    for category in categories:
        id_category = category.get("id_category")
        cat = CategoryModel.get_by_id(category_id=id_category)
        values = cat.calc_price(descuento=porcentaje_descuento)
        price = values.get("precio_final")
        total_price += price
    
    
    
    return total_price


# ==========================================
# ASYNC TASKS
# ==========================================

def process_payu_transaction(app, data):
    """
    Background task to process PayU confirmation logic.
    """
    with app.app_context():
        try:
            merchant_id = data.get("merchant_id")
            reference_sale = data.get("reference_sale")
            value = data.get("value")
            # currency = data.get("currency")
            state_pol = data.get("state_pol")
            # received_sign = data.get("sign")

            # Validate locally again if needed, though simpler checks are done in route
            if not all([merchant_id, reference_sale, value, state_pol]):
                 logger.error("Missing parameters in async task")
                 return

            # Campos extra a procesar
            extra_fields = ["extra1", "extra2", "extra3", "extra4"]

            cart_data_list = []
            for field in extra_fields:
                raw_value = data.get(field)
                if raw_value:  # si viene None o cadena vacía, lo ignora
                    cart_data_list.append(parse_data(raw_value, reference_sale, value))

            logger.info(f"Processing PayU transaction async: {cart_data_list}")

            # Si está aprobada, procesamos cada lista
            if state_pol == "4":
                for cart_data in cart_data_list:
                    if isinstance(cart_data, list):
                        revisarYGuardarInformacionDePago(cart_data)
                        verificarYActualizarVendedor(cart_data)
            
            logger.info("Async PayU processing completed successfully")

        except Exception as e:
            logger.error(f"Error in async PayU task: {e}")


def process_paypal_payment(app, data):
    """
    Background task to process PayPal webhook logic.
    """
    with app.app_context():
        try:
            resource = data.get("resource", {})
            payment_id = resource.get("id")
            payer_id = resource.get("payer", {}).get("payer_info", {}).get("payer_id")
            
            registerPayment=[]
            for item in resource["transactions"]:
                registerCode=item.get('description')
                # Note: Assuming this does DB lookup
                registerPayment = PaymentRegisterRepository.getItemsPayment(registerCode)
             
            registrosParceados= generarObjetoParaGuardarLosRegistroDePago(registerPayment, payment_id)

            # DB updates
            revisarYGuardarInformacionDePago(registrosParceados)
            registrarPagoPagado(registerPayment)
            verificarYActualizarVendedor(registrosParceados)
            
            # Execute payment on PayPal
            payment = paypalrestsdk.Payment.find(payment_id)
            if payment.execute({"payer_id": payer_id}):
                logger.info(f"PayPal payment {payment_id} captured and processed successfully.")
            else:
                logger.error(f"Failed to execute PayPal payment {payment_id}: {payment.error}")

        except Exception as e:
            logger.error(f"Error in async PayPal task: {e}")


# ==========================================
# ROUTES
# ==========================================

@payments_bp.route("/payu-confirmation", methods=["POST"])
def payu_confirmation():
    try:
        data = request.form.to_dict()

        merchant_id = data.get("merchant_id")
        reference_sale = data.get("reference_sale")
        value = data.get("value")
        currency = data.get("currency")
        state_pol = data.get("state_pol")
        received_sign = data.get("sign")
        
        if not all([merchant_id, reference_sale, value, currency, state_pol, received_sign]):
            return jsonify({"error": "Missing parameters"}), 400
        
        transaction_status = "approved" if state_pol == "4" else "rejected"

        # Offload heavy processing to thread pool
        app = current_app._get_current_object() # Pass the real app object, not the proxy
        executor.submit(process_payu_transaction, app, data)

        return jsonify({
            "message": "Confirmation received",
            "transaction_status": transaction_status
        }), 200

    except Exception as e:
        logger.error(f"Error in payu_confirmation route: {e}")
        return jsonify({"message": "Confirmation received", "transaction_status": "error"}), 200


@payments_bp.route("/paypal/webhook", methods=["POST"])
def paypal_webhook():
    try:
        data = request.json
        event_type = data.get("event_type")

        if event_type == "PAYMENTS.PAYMENT.CREATED":
            app = current_app._get_current_object()
            executor.submit(process_paypal_payment, app, data)
            
            return jsonify({"status": "processing", "message": "Webhook received, processing in background"}), 200

        if event_type == "PAYMENT.SALE.REFUNDED":
            resource = data.get("resource", {})
            refund_id = resource.get("id")
            parent_payment = resource.get("parent_payment")
            amount = resource.get("amount", {})

            return jsonify({
                "status": "refund_received",
                "refund_id": refund_id,
                "parent_payment": parent_payment,
                "amount": amount
            }), 200

        if event_type == "PAYMENT.SALE.REVERSED":
            resource = data.get("resource", {})
            return jsonify({
                "status": "reversed",
                "resource": resource
            }), 200


        return jsonify({"status": "ignored", "event": event_type}), 200

    except Exception as e:
        logger.error(f"Error in paypal_webhook route: {e}")
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
            print("cupon", cupon)


            user=UserModel.validar_cupon(cupon)

            if not user:
                return jsonify({"message": "No tienes cupon"}), 400

            precio = calculate_total_price(categories, user.descuento_referido)
            descuento_aplicado = user.descuento_referido
            firm= PaymentRespository(price=precio)
            firm.generate_firm()

            user_country = (session.get("user", {}).get("country") or "").upper()
            cambio_dolar_raw = SystemVariable.query.filter_by(campo_codigo="CAMBIO_DOLAR").first()
            try:
                cambio_dolar = float(cambio_dolar_raw.dato) if cambio_dolar_raw and cambio_dolar_raw.dato else 1.0
            except (TypeError, ValueError):
                cambio_dolar = 1.0

            # Para usuarios de Colombia mantenemos el precio original.
            # Para otros países convertimos usando CAMBIO_DOLAR.
            if user_country == "CO":
                response_price = firm.price
            else:
                response_price = firm.price / cambio_dolar if cambio_dolar else firm.price

            return jsonify({
                "status": "success",
                "message": "OK",
                "records": [{
                    "signature": firm.signature, 
                    "reference_code":firm.reference_code, 
                    "price": response_price,
                    "google_id":user.google_id,
                    "cupon":cupon,
                    "descuento":response_price * (descuento_aplicado/100)
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





# Variables globales para cachear la tasa de cambio
_exchange_rate_cache = {
    "rate": None,
    "counter": 100  # Iniciar en 100 para forzar la primera actualización
}

def get_cop_to_usd_rate():
    global _exchange_rate_cache
    
    # Actualizar si no hay tasa o si el contador llega a 100
    if _exchange_rate_cache["rate"] is None or _exchange_rate_cache["counter"] >= 100:
        try:
            response = requests.get("https://api.exchangerate-api.com/v4/latest/COP", timeout=5)
            response.raise_for_status()
            data = response.json()
            _exchange_rate_cache["rate"] = data["rates"]["USD"]
            _exchange_rate_cache["counter"] = 0  # Reiniciar contador

            # Actualizar variable del sistema CAMBIO_DOLAR
            try:
                 # La API retorna valor de 1 COP en USD (ej: 0.00025).
                 # CAMBIO_DOLAR suele ser cuandos COP es 1 USD (ej: 4000).
                 rate_usd = _exchange_rate_cache["rate"]
                 if rate_usd:
                    tasa_cop = 1 / rate_usd
                    var = SystemVariable.query.filter_by(campo_codigo="CAMBIO_DOLAR").first()
                    if var:
                        var.dato = str(tasa_cop)
                        db.session.commit()
                        # print(f"Variable CAMBIO_DOLAR actualizada a: {tasa_cop}")
            except Exception as db_e:
                print(f"Error updating CAMBIO_DOLAR system variable: {db_e}")
                db.session.rollback()
        except Exception as e:
            print(f"Error fetching exchange rate: {e}. Using fallback.")
            if _exchange_rate_cache["rate"] is None:
                return 1 / 4000  # Fallback: 4000 COP = 1 USD
            # Si falla, mantenemos el valor anterior (si existe) y reseteamos contador
            # para evitar reintentos continuos que ralenticen el sistema.
            _exchange_rate_cache["counter"] = 0

    _exchange_rate_cache["counter"] += 1
    return _exchange_rate_cache["rate"]

def generate_link_worker(app, categories, google_id):
    with app.app_context():
        try:
            precio, items, paypal_items = calculate_total_price_and_items(categories, google_id=google_id, porcentaje_descuento=0)
            rate = get_cop_to_usd_rate()
            precio_usd = precio * rate
            
            for item in paypal_items:
                item_price_cop = float(item["price"])
                item["price"] = f"{item_price_cop * rate:.2f}"

            ref_code = str(uuid.uuid4())[:20]
            PaymentRegisterRepository.create_pending(items, ref_code)
            
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": f"http://localhost:5002/paypal/return?ref={ref_code}",
                    "cancel_url": "http://localhost:5002/paypal/cancel"
                },
                "transactions": [{
                    "item_list": {
                        "items": paypal_items
                    },
                    "amount": {
                        "total": f"{precio_usd:.2f}",
                        "currency": "USD"
                    },
                    "description": f"{ref_code}"
                }]
            })

            if payment.create():
                for link in payment.links:
                    if link.method == "REDIRECT":
                        return {"status": "success", "approval_url": link.href}
                return {"status": "error", "message": "No se encontró link de aprobación", "code": 500}
            else:
                return {"status": "error", "message": payment.error, "code": 400}

        except Exception as e:
            print("Error PayPal Worker:", e)
            return {"status": "error", "message": "error", "code": 500}

def generate_link_coupon_worker(app, categories, google_id, cupon):
    with app.app_context():
        try:
            user = UserModel.validar_cupon(cupon)

            if not user:
                return {"status": "error", "message": "No tienes cupon", "code": 400}

            precio, items, paypal_items = calculate_total_price_and_items(categories, google_id=google_id, google_id_refer=user.google_id, porcentaje_descuento=user.descuento_referido)

            rate = get_cop_to_usd_rate()
            precio_usd = precio * rate

            for item in paypal_items:
                item_price_cop = float(item["price"])
                item["price"] = f"{item_price_cop * rate:.2f}"

            ref_code = str(uuid.uuid4())[:20]
            PaymentRegisterRepository.create_pending(items, ref_code)
            
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": f"http://localhost:5002/paypal/return?ref={ref_code}",
                    "cancel_url": "http://localhost:5002/paypal/cancel"
                },
                "transactions": [{
                    "item_list": {
                        "items": paypal_items
                    },
                    "amount": {
                        "total": f"{precio_usd:.2f}",
                        "currency": "USD"
                    },
                    "description": f"{ref_code}"
                }]
            })

            if payment.create():
                for link in payment.links:
                    if link.method == "REDIRECT":
                        return {"status": "success", "approval_url": link.href}
                return {"status": "error", "message": "No se encontró link de aprobación", "code": 500}
            else:
                return {"status": "error", "message": payment.error, "code": 400}

        except Exception as e:
            print("Error PayPal Worker (Coupon):", e)
            return {"status": "error", "message": "error", "code": 500}



@payments_bp.route("/paypal-generate-link-pay", methods=["POST"])
async def paypal_generate_link_pay():
    try:
        # Validar sesión si es necesario
        # isLoggin = validarSeccionUsuario()
        # if isLoggin: return isLoggin

        data = request.get_json()
        categories = data["categories"]
        google_id = session["user"]["google_id"]

        loop = asyncio.get_event_loop()
        app = current_app._get_current_object()
        
        result = await loop.run_in_executor(executor, generate_link_worker, app, categories, google_id)

        if result["status"] == "success":
            return jsonify({"approval_url": result["approval_url"]}), 200
        else:
            return jsonify(result.get("message", "Error")), result.get("code", 500)

    except Exception as e:
        print("Error PayPal:", e)
        return jsonify({"message": "error"}), 500

@payments_bp.route("/paypal-generate-link-pay-cupon", methods=["POST"])
async def paypal_generate_link_pay_cupon():
    try:
        # Validar sesión si es necesario
        # isLoggin = validarSeccionUsuario()
        # if isLoggin: return isLoggin

        data = request.get_json()
        categories = data["categories"]
        cupon = data["cupon"]
        print("cupon", cupon)
        google_id = session["user"]["google_id"]

        loop = asyncio.get_event_loop()
        app = current_app._get_current_object()

        result = await loop.run_in_executor(executor, generate_link_coupon_worker, app, categories, google_id, cupon)

        if result["status"] == "success":
            return jsonify({"approval_url": result["approval_url"]}), 200
        else:
            return jsonify(result.get("message", "Error")), result.get("code", 500)

    except Exception as e:
        print("Error PayPal:", e)
        return jsonify({"message": "error"}), 500

@payments_bp.route("/paypal-generate-link-pay-external", methods=["POST"])
async def paypal_generate_link_pay_external():
    try:
        # Validar sesión si es necesario
        # isLoggin = validarSeccionUsuario()
        # if isLoggin: return isLoggin

        data = request.get_json()
        categories = data["categories"]
        google_id = data["google_id_external"]

        loop = asyncio.get_event_loop()
        app = current_app._get_current_object()
        
        result = await loop.run_in_executor(executor, generate_link_worker, app, categories, google_id)

        if result["status"] == "success":
            return jsonify({"approval_url": result["approval_url"]}), 200
        else:
            return jsonify(result.get("message", "Error")), result.get("code", 500)

    except Exception as e:
        print("Error PayPal:", e)
        return jsonify({"message": "error"}), 500


