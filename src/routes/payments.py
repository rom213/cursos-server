import asyncio
import hashlib
import logging
import uuid
from typing import Any

import paypalrestsdk
import requests
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from config import settings
from database import get_db, session_scope
from models import db
from models.Category import TipoCategoria
from models.PaymentResgister import PaymentRegister
from models.SystemVariable import SystemVariable
from models.User import TipoUsuario
from servises.categories.category_model import CategoryModel
from servises.groups.repository import GroupRepository
from servises.payment.payment_repository import PaymentRespository
from servises.payment_register.payment_register_repository import PaymentRegisterRepository
from servises.Users.user_model import UserModel
from utils.async_executor import executor
from utils.auth import get_current_user_payload, get_google_id

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

paypalrestsdk.configure(
    {
        "mode": settings.PAYPAL_MODE,
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET,
    }
)

router = APIRouter(tags=["payments"])


# ==========================================
# HELPERS
# ==========================================


def parse_data(dat: str, reference_sale: str, pay_value: str) -> list:
    items = dat.strip("|").split("|")
    parsed = []
    for item in items:
        parts = item.split(",")
        try:
            category_id = int(parts[0].replace(".", ""))
        except (ValueError, IndexError):
            logger.warning("parse_data: category_id inválido — valor recibido: %r", parts[0] if parts else dat)
            continue
        parsed.append(
            {
                "category_id": category_id,
                "google_id": parts[1] if len(parts) > 1 else None,
                "google_id_refer": parts[2] if len(parts) > 2 else None,
                "reference_code": reference_sale,
                "pay_value_refer": pay_value,
            }
        )
    return parsed


def calculate_total_price_and_items(
    categories: list,
    google_id: str = "118070327157829661695",
    google_id_refer: str | None = None,
    porcentaje_descuento: float = 0,
) -> tuple:
    total_price = 0.0
    payment_items = []
    paypal_items = []

    for category in categories:
        id_category = category.get("id_category")
        cat = CategoryModel.get_by_id(category_id=id_category)
        values = cat.calc_price(descuento=porcentaje_descuento)
        price = values.get("precio_final")
        total_price += price

        payment_items.append(
            {
                "category_id": id_category,
                "google_id": google_id,
                "google_id_refer": google_id_refer,
                "pay_value_refer": price,
                "moneda": "USD",
            }
        )
        paypal_items.append(
            {
                "name": getattr(cat, "titulo", f"Category {id_category}"),
                "sku": f"cat_{id_category}",
                "price": f"{price:.2f}",
                "currency": "USD",
                "quantity": 1,
            }
        )

    return total_price, payment_items, paypal_items


def calculate_total_price(categories: list, porcentaje_descuento: float = 0) -> float:
    total_price = 0.0
    for category in categories:
        id_category = category.get("id_category")
        cat = CategoryModel.get_by_id(category_id=id_category)
        values = cat.calc_price(descuento=porcentaje_descuento)
        total_price += values.get("precio_final")
    return total_price


def registrar_pago_pagado(registros: list) -> None:
    for item in registros:
        item.cambiarStatus()


def generar_objeto_para_guardar_registros(registros: list, payment_id: str) -> list:
    return [
        {
            "category_id": int(item.category_id),
            "google_id": item.google_id,
            "google_id_refer": item.google_id_refer,
            "reference_code": payment_id,
            "pay_value_refer": item.pay_value_refer,
        }
        for item in registros
    ]


def revisar_y_guardar_informacion_de_pago(registros: list) -> None:
    for item in registros:
        try:
            GroupRepository.process_member_addition("agregar_miembro_grupo", data=item)
        except Exception as e:
            logger.error(f"Error procesando {item}: {e}")


def verificar_y_actualizar_vendedor(registros: list) -> None:
    try:
        target_categories = [TipoCategoria.CAT_1, TipoCategoria.CAT_2]
        for item in registros:
            category_id = item.get("category_id")
            google_id = item.get("google_id")
            if not category_id or not google_id:
                continue
            category = CategoryModel.get_by_id(category_id)
            if not category:
                continue
            if category.tipo_categoria in target_categories:
                user = UserModel.get_by_google_id(google_id)
                if user and user.tipo_usuario != TipoUsuario.VENDEDOR:
                    logger.info(f"Actualizando usuario {google_id} a VENDEDOR")
                    user.update(tipo_usuario=TipoUsuario.VENDEDOR)
    except Exception as e:
        logger.error(f"Error al verificar/actualizar vendedor: {e}")


# ==========================================
# CACHE TASA DE CAMBIO
# ==========================================

_exchange_rate_cache: dict[str, Any] = {"rate": None, "counter": 100}


def get_cop_to_usd_rate() -> float:
    global _exchange_rate_cache

    if _exchange_rate_cache["rate"] is None or _exchange_rate_cache["counter"] >= 100:
        try:
            response = requests.get(
                "https://api.exchangerate-api.com/v4/latest/COP", timeout=5
            )
            response.raise_for_status()
            data = response.json()
            _exchange_rate_cache["rate"] = data["rates"]["USD"]
            _exchange_rate_cache["counter"] = 0

            try:
                rate_usd = _exchange_rate_cache["rate"]
                if rate_usd:
                    tasa_cop = 1 / rate_usd
                    var = SystemVariable.query.filter_by(campo_codigo="CAMBIO_DOLAR").first()
                    if var:
                        var.dato = str(tasa_cop)
                        db.session.commit()
            except Exception as db_e:
                logger.error(f"Error updating CAMBIO_DOLAR: {db_e}")
                db.session.rollback()

        except Exception as e:
            logger.error(f"Error fetching exchange rate: {e}")
            if _exchange_rate_cache["rate"] is None:
                return 1 / 4000
            _exchange_rate_cache["counter"] = 0

    _exchange_rate_cache["counter"] += 1
    return _exchange_rate_cache["rate"]


# ==========================================
# BACKGROUND TASKS (sin app_context)
# ==========================================


def process_payu_transaction(data: dict) -> None:
    with session_scope():
        try:
            merchant_id = data.get("merchant_id")
            reference_sale = data.get("reference_sale")
            value = data.get("value")
            state_pol = data.get("state_pol")

            if not all([merchant_id, reference_sale, value, state_pol]):
                logger.error("Missing parameters in async task")
                return

            extra_fields = ["extra1", "extra2", "extra3", "extra4"]
            cart_data_list = []
            for field in extra_fields:
                raw_value = data.get(field)
                if raw_value:
                    cart_data_list.append(parse_data(raw_value, reference_sale, value))

            logger.info(f"Processing PayU transaction: {cart_data_list}")

            if state_pol == "4":
                for cart_data in cart_data_list:
                    if isinstance(cart_data, list):
                        revisar_y_guardar_informacion_de_pago(cart_data)
                        verificar_y_actualizar_vendedor(cart_data)

            logger.info("PayU processing completed successfully")

        except Exception as e:
            logger.error(f"Error in PayU task: {e}")


def process_paypal_payment(data: dict) -> None:
    with session_scope():
        try:
            resource = data.get("resource", {})
            payment_id = resource.get("id")
            payer_id = (
                resource.get("payer", {}).get("payer_info", {}).get("payer_id")
            )
            register_payment: list = []
            for item in resource.get("transactions", []):
                register_code = item.get("description")
                register_payment = PaymentRegisterRepository.getItemsPayment(register_code)

            registros_parceados = generar_objeto_para_guardar_registros(
                register_payment, payment_id
            )
            
            
            revisar_y_guardar_informacion_de_pago(registros_parceados)
            registrar_pago_pagado(register_payment)
            verificar_y_actualizar_vendedor(registros_parceados)

            payment = paypalrestsdk.Payment.find(payment_id)
            if payment.execute({"payer_id": payer_id}):
                logger.info(f"PayPal payment {payment_id} captured successfully.")
            else:
                logger.error(f"Failed to execute PayPal payment {payment_id}: {payment.error}")

        except Exception as e:
            logger.error(f"Error in PayPal task: {e}")


def generate_link_worker(categories: list, google_id: str) -> dict:
    with session_scope():
        try:
            precio, items, paypal_items = calculate_total_price_and_items(
                categories, google_id=google_id, porcentaje_descuento=0
            )
            rate = get_cop_to_usd_rate()
            precio_usd = precio * rate

            for item in paypal_items:
                item["price"] = f"{float(item['price']) * rate:.2f}"

            ref_code = str(uuid.uuid4())[:20]
            PaymentRegisterRepository.create_pending(items, ref_code)

            payment = paypalrestsdk.Payment(
                {
                    "intent": "sale",
                    "payer": {"payment_method": "paypal"},
                    "redirect_urls": {
                        "return_url": f"http://localhost:5002/paypal/return?ref={ref_code}",
                        "cancel_url": "http://localhost:5002/paypal/cancel",
                    },
                    "transactions": [
                        {
                            "item_list": {"items": paypal_items},
                            "amount": {"total": f"{precio_usd:.2f}", "currency": "USD"},
                            "description": ref_code,
                        }
                    ],
                }
            )

            if payment.create():
                for link in payment.links:
                    if link.method == "REDIRECT":
                        return {"status": "success", "approval_url": link.href}
                return {"status": "error", "message": "No approval link found", "code": 500}
            else:
                return {"status": "error", "message": payment.error, "code": 400}

        except Exception as e:
            logger.error(f"Error PayPal Worker: {e}")
            return {"status": "error", "message": "error", "code": 500}


def generate_link_coupon_worker(categories: list, google_id: str, cupon: str) -> dict:
    with session_scope():
        try:
            user = UserModel.validar_cupon(cupon)
            if not user:
                return {"status": "error", "message": "No tienes cupon", "code": 400}

            precio, items, paypal_items = calculate_total_price_and_items(
                categories,
                google_id=google_id,
                google_id_refer=user.google_id,
                porcentaje_descuento=user.descuento_referido,
            )
            rate = get_cop_to_usd_rate()
            precio_usd = precio * rate

            for item in paypal_items:
                item["price"] = f"{float(item['price']) * rate:.2f}"

            ref_code = str(uuid.uuid4())[:20]
            PaymentRegisterRepository.create_pending(items, ref_code)

            payment = paypalrestsdk.Payment(
                {
                    "intent": "sale",
                    "payer": {"payment_method": "paypal"},
                    "redirect_urls": {
                        "return_url": f"http://localhost:5002/paypal/return?ref={ref_code}",
                        "cancel_url": "http://localhost:5002/paypal/cancel",
                    },
                    "transactions": [
                        {
                            "item_list": {"items": paypal_items},
                            "amount": {"total": f"{precio_usd:.2f}", "currency": "USD"},
                            "description": ref_code,
                        }
                    ],
                }
            )

            if payment.create():
                for link in payment.links:
                    if link.method == "REDIRECT":
                        return {"status": "success", "approval_url": link.href}
                return {"status": "error", "message": "No approval link found", "code": 500}
            else:
                return {"status": "error", "message": payment.error, "code": 400}

        except Exception as e:
            logger.error(f"Error PayPal Worker (Coupon): {e}")
            return {"status": "error", "message": "error", "code": 500}


# ==========================================
# ROUTES
# ==========================================


@router.post("/payu-confirmation")
async def payu_confirmation(request: Request, background_tasks: BackgroundTasks):
    try:
        form = await request.form()
        data = dict(form)

        required = ["merchant_id", "reference_sale", "value", "currency", "state_pol", "sign"]
        if not all(data.get(f) for f in required):
            raise HTTPException(status_code=400, detail="Missing parameters")

        transaction_status = "approved" if data.get("state_pol") == "4" else "rejected"
        background_tasks.add_task(process_payu_transaction, data)

        return {
            "message": "Confirmation received",
            "transaction_status": transaction_status,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in payu_confirmation: {e}")
        return {"message": "Confirmation received", "transaction_status": "error"}


@router.post("/paypal/webhook")
async def paypal_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=422,
                detail="El cuerpo JSON debe ser un objeto",
            )
        event_type = data.get("event_type")

        if event_type == "PAYMENTS.PAYMENT.CREATED":
            background_tasks.add_task(process_paypal_payment, data)
            return {
                "status": "processing",
                "message": "Webhook received, processing in background",
            }

        if event_type == "PAYMENT.SALE.REFUNDED":
            resource = data.get("resource", {})
            return {
                "status": "refund_received",
                "refund_id": resource.get("id"),
                "parent_payment": resource.get("parent_payment"),
                "amount": resource.get("amount", {}),
            }

        if event_type == "PAYMENT.SALE.REVERSED":
            return {"status": "reversed", "resource": data.get("resource", {})}

        return {"status": "ignored", "event": event_type}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in paypal_webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payu-firm")
def payu_signature(
    body: dict = Body(...),
    google_id: str = Depends(get_google_id),
    db: Session = Depends(get_db),
):
    try:
        categories = body["categories"]
        precio = calculate_total_price(categories)
        firm = PaymentRespository(price=precio)
        firm.generate_firm()
        return {
            "signature": firm.signature,
            "reference_code": firm.reference_code,
            "price": firm.price,
        }
    except Exception:
        return {"message": "posible error verificar"}


@router.post("/payu-firm-cupon")
def payu_signature_cupon(
    body: dict = Body(...),
    user: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    try:
        categories = body["categories"]
        cupon = body["cupon"]

        user_obj = UserModel.validar_cupon(cupon)
        if not user_obj:
            return {"message": "No tienes cupon"}

        precio = calculate_total_price(categories, user_obj.descuento_referido)
        descuento_aplicado = user_obj.descuento_referido
        firm = PaymentRespository(price=precio)
        firm.generate_firm()

        user_country = (user.get("country") or "").upper()
        cambio_dolar_raw = SystemVariable.query.filter_by(campo_codigo="CAMBIO_DOLAR").first()
        try:
            cambio_dolar = (
                float(cambio_dolar_raw.dato)
                if cambio_dolar_raw and cambio_dolar_raw.dato
                else 1.0
            )
        except (TypeError, ValueError):
            cambio_dolar = 1.0

        response_price = (
            firm.price
            if user_country == "CO"
            else (firm.price / cambio_dolar if cambio_dolar else firm.price)
        )

        return {
            "status": "success",
            "message": "OK",
            "records": [
                {
                    "signature": firm.signature,
                    "reference_code": firm.reference_code,
                    "price": response_price,
                    "google_id": user_obj.google_id,
                    "cupon": cupon,
                    "descuento": response_price * (descuento_aplicado / 100),
                }
            ],
        }
    except Exception as e:
        logger.error(f"Error payu-firm-cupon: {e}")
        return {"message": "posible error verificar"}


@router.post("/paypal/return")
@router.get("/paypal/return")
def paypal_return():
    return {"status": "ok"}


@router.post("/paypal-generate-link-pay")
async def paypal_generate_link_pay(
    body: dict = Body(...),
    google_id: str = Depends(get_google_id),
):
    try:
        categories = body["categories"]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, generate_link_worker, categories, google_id
        )
        if result["status"] == "success":
            return {"approval_url": result["approval_url"]}
        return {"message": result.get("message", "Error")}
    except Exception as e:
        logger.error(f"Error PayPal: {e}")
        return {"message": "error"}


@router.post("/paypal-generate-link-pay-cupon")
async def paypal_generate_link_pay_cupon(
    body: dict = Body(...),
    google_id: str = Depends(get_google_id),
):
    try:
        categories = body["categories"]
        cupon = body["cupon"]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, generate_link_coupon_worker, categories, google_id, cupon
        )
        if result["status"] == "success":
            return {"approval_url": result["approval_url"]}
        return {"message": result.get("message", "Error")}
    except Exception as e:
        logger.error(f"Error PayPal: {e}")
        return {"message": "error"}


@router.post("/paypal-generate-link-pay-external")
async def paypal_generate_link_pay_external(body: dict = Body(...)):
    try:
        categories = body["categories"]
        google_id = body["google_id_external"]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, generate_link_worker, categories, google_id
        )
        if result["status"] == "success":
            return {"approval_url": result["approval_url"]}
        return {"message": result.get("message", "Error")}
    except Exception as e:
        logger.error(f"Error PayPal: {e}")
        return {"message": "error"}
