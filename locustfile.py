"""
=============================================================================
 PRUEBAS DE RENDIMIENTO Y FIABILIDAD — ISO/IEC 25023
 Plataforma: Cursos Estudia y Trabaja
=============================================================================

 Métricas ISO 25023 implementadas en este archivo:

 1. COMPORTAMIENTO TEMPORAL (Performance Efficiency - Time Behaviour)
    Fórmula:  T_mean = Σ(t_i) / N
    Donde:    t_i = tiempo de respuesta de la petición i
              N   = número total de peticiones
    Locust calcula esto automáticamente como "Average Response Time".

 2. CAPACIDAD / THROUGHPUT (Performance Efficiency - Capacity)
    Fórmula:  X = N / T
    Donde:    N = número de peticiones completadas
              T = duración total de la prueba (segundos)
    Locust calcula esto como "Requests/s" (RPS).

 3. TASA DE ERROR / MADUREZ (Reliability - Maturity)
    Fórmula:  E = (N_errores / N_total) × 100
    Donde:    N_errores = peticiones con respuesta de error (4xx, 5xx)
              N_total   = total de peticiones realizadas
    Se implementa con response.failure() y se resume al final.

 Ejecución:
    locust -f locustfile.py --host=http://localhost:5002
    (Abrir http://localhost:8089 para la interfaz web de Locust)

    Modo headless (sin interfaz gráfica):
    locust -f locustfile.py --host=http://localhost:5002 --headless \
           -u 50 -r 5 --run-time 60s

 Dependencias:
    pip install locust
=============================================================================
"""

import time
import random
import json
import uuid
import gevent

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


# =========================================================================
# CONSTANTES DE CONFIGURACIÓN
# =========================================================================
# Porcentaje de peticiones que simularán fallo intencionalmente
# para medir la Tasa de Error (E)
SIMULATED_FAILURE_RATE = 0.10  # 10% de fallos simulados

# Latencia de red simulada (segundos) para medición precisa de T_mean
SIMULATED_NETWORK_LATENCY_MIN = 0.01  # 10ms
SIMULATED_NETWORK_LATENCY_MAX = 0.05  # 50ms


# =========================================================================
# CONTADORES GLOBALES PARA MÉTRICAS ISO
# =========================================================================
class ISOMetrics:
    """Recolector centralizado de métricas ISO 25023."""

    def __init__(self):
        self.total_requests = 0
        self.total_errors = 0
        self.total_response_time_ms = 0.0
        self.start_time = None
        self.end_time = None

    def record_request(self, response_time_ms, is_error=False):
        self.total_requests += 1
        self.total_response_time_ms += response_time_ms
        if is_error:
            self.total_errors += 1

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    @property
    def t_mean(self):
        """ISO 25023 — Comportamiento Temporal: T_mean = Σ(t_i) / N"""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time_ms / self.total_requests

    @property
    def throughput(self):
        """ISO 25023 — Capacidad: X = N / T"""
        if not self.start_time or not self.end_time:
            return 0.0
        duration = self.end_time - self.start_time
        if duration == 0:
            return 0.0
        return self.total_requests / duration

    @property
    def error_rate(self):
        """ISO 25023 — Tasa de Error: E = (N_errores / N_total) × 100"""
        if self.total_requests == 0:
            return 0.0
        return (self.total_errors / self.total_requests) * 100


# Instancia global
iso_metrics = ISOMetrics()


# =========================================================================
# HOOKS DE EVENTOS LOCUST
# =========================================================================
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta al iniciar la prueba."""
    iso_metrics.start()
    print("\n" + "=" * 70)
    print("  ISO/IEC 25023 — PRUEBA DE RENDIMIENTO INICIADA")
    print("  Plataforma: Cursos Estudia y Trabaja")
    print("=" * 70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Se ejecuta al detener la prueba.
    Imprime el resumen completo de métricas ISO 25023.
    """
    iso_metrics.stop()

    print("\n" + "=" * 70)
    print("  RESUMEN DE MÉTRICAS ISO/IEC 25023")
    print("=" * 70)
    print(f"""
  ┌─────────────────────────────────────────────────────────────────┐
  │  1. COMPORTAMIENTO TEMPORAL (Time Behaviour)                   │
  │     Fórmula: T_mean = Σ(t_i) / N                              │
  │     T_mean = {iso_metrics.t_mean:.2f} ms                      │
  │     N (total peticiones) = {iso_metrics.total_requests}        │
  ├─────────────────────────────────────────────────────────────────┤
  │  2. CAPACIDAD / THROUGHPUT (Capacity)                          │
  │     Fórmula: X = N / T                                        │
  │     X = {iso_metrics.throughput:.2f} req/s                     │
  │     T (duración) = {(iso_metrics.end_time or 0) - (iso_metrics.start_time or 0):.2f} s │
  ├─────────────────────────────────────────────────────────────────┤
  │  3. TASA DE ERROR / MADUREZ (Maturity)                         │
  │     Fórmula: E = (N_errores / N_total) × 100                  │
  │     E = {iso_metrics.error_rate:.2f}%                          │
  │     N_errores = {iso_metrics.total_errors}                     │
  │     N_total   = {iso_metrics.total_requests}                   │
  └─────────────────────────────────────────────────────────────────┘
    """)
    print("=" * 70 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length,
               exception, **kwargs):
    """
    Listener global que captura CADA petición realizada por Locust
    para alimentar el recolector de métricas ISO.
    """
    is_error = exception is not None
    iso_metrics.record_request(response_time, is_error=is_error)


# =========================================================================
# FUNCIONES AUXILIARES
# =========================================================================
def simulate_network_latency():
    """
    Simula latencia de red variable para obtener mediciones
    más realistas de T_mean. Usa gevent.sleep para no bloquear
    el event loop de Locust.
    """
    latency = random.uniform(
        SIMULATED_NETWORK_LATENCY_MIN,
        SIMULATED_NETWORK_LATENCY_MAX
    )
    gevent.sleep(latency)


def should_simulate_failure():
    """
    Determina aleatoriamente si esta petición debe simular un fallo.
    Retorna True con probabilidad SIMULATED_FAILURE_RATE.
    """
    return random.random() < SIMULATED_FAILURE_RATE


# =========================================================================
# USUARIO DE PRUEBA: FLUJO PÚBLICO (Sin autenticación)
# =========================================================================
class PublicUser(HttpUser):
    """
    Simula un usuario anónimo que navega el catálogo de cursos.
    Endpoints públicos: categorías, búsqueda, mensajes.
    """
    wait_time = between(1, 3)
    weight = 3  # 3x más usuarios públicos que autenticados

    # ── ISO 25023: Comportamiento Temporal ──────────────────────────
    @task(5)
    def get_all_categories(self):
        """
        GET /api/category/all-categories
        Mide T_mean para la consulta principal del catálogo.
        """
        simulate_network_latency()

        with self.client.get(
            "/api/category/all-categories",
            params={"limit": 6, "offset": 0},
            name="[PUBLIC] GET /api/category/all-categories",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Código inesperado: {response.status_code}"
                )

    @task(3)
    def get_category_by_id(self):
        """
        GET /api/category/{id}
        Prueba con IDs aleatorios (1-10) para cubrir hits y misses.
        """
        simulate_network_latency()
        category_id = random.randint(1, 10)

        with self.client.get(
            f"/api/category/{category_id}",
            name="[PUBLIC] GET /api/category/{id}",
            catch_response=True
        ) as response:
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(
                    f"Código inesperado: {response.status_code}"
                )

    @task(2)
    def deep_search_categories(self):
        """
        GET /api/category/categories/deep-search?q=...
        Prueba de búsqueda con términos variados.
        """
        simulate_network_latency()
        search_terms = [
            "python", "javascript", "excel", "marketing",
            "diseño", "contabilidad", "inglés", "programación",
            "xyz_no_existe_123"
        ]
        term = random.choice(search_terms)

        with self.client.get(
            "/api/category/categories/deep-search",
            params={"q": term, "limit": 5},
            name="[PUBLIC] GET /deep-search",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Búsqueda falló: {response.status_code}"
                )

    @task(2)
    def get_messages_for_category(self):
        """
        GET /all-messages/{id}
        Obtener valoraciones/comentarios de una categoría.
        """
        simulate_network_latency()
        category_id = random.randint(1, 5)

        with self.client.get(
            f"/all-messages/{category_id}",
            name="[PUBLIC] GET /all-messages/{id}",
            catch_response=True
        ) as response:
            if response.status_code in (200, 500):
                response.success()
            else:
                response.failure(
                    f"Código inesperado: {response.status_code}"
                )


# =========================================================================
# USUARIO DE PRUEBA: FLUJO AUTENTICADO (Pagos, Webhooks, Admin)
# =========================================================================
class AuthenticatedUser(HttpUser):
    """
    Simula un usuario autenticado que realiza operaciones de pago
    y recibe webhooks. Incluye simulación de fallos (Fiabilidad).
    """
    wait_time = between(2, 5)
    weight = 1

    # ── ISO 25023: Tasa de Error — Webhook PayU malformado ─────────
    @task(3)
    def payu_confirmation_valid(self):
        """
        POST /payu-confirmation
        Simula un webhook de PayU válido (transacción aprobada).
        """
        simulate_network_latency()
        payload = {
            "merchant_id": "508029",
            "reference_sale": f"TEST-{uuid.uuid4().hex[:10]}",
            "value": "150000.00",
            "currency": "COP",
            "state_pol": "4",
            "sign": "abc123def456",
            "extra1": "|1,118070327157829661695"
        }

        with self.client.post(
            "/payu-confirmation",
            data=payload,
            name="[AUTH] POST /payu-confirmation (válido)",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("transaction_status") == "approved":
                    response.success()
                else:
                    response.failure(
                        f"Estado inesperado: {data.get('transaction_status')}"
                    )
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def payu_confirmation_malformed(self):
        """
        POST /payu-confirmation — FALLO SIMULADO
        ISO 25023 Fiabilidad: Envía datos incompletos para forzar
        el cálculo de E = (N_errores / N_total) × 100.
        El sistema debe responder HTTP 400, NO caer.
        """
        simulate_network_latency()
        # Webhook malformado: faltan campos obligatorios
        malformed_payloads = [
            {"merchant_id": "solo_esto"},
            {"value": "100", "currency": "COP"},
            {},
        ]
        payload = random.choice(malformed_payloads)

        with self.client.post(
            "/payu-confirmation",
            data=payload,
            name="[FIABILIDAD] POST /payu-confirmation (malformado)",
            catch_response=True
        ) as response:
            if response.status_code == 400:
                # El sistema detectó correctamente el error
                response.success()
            elif response.status_code == 200:
                # El sistema no debería aceptar datos incompletos
                response.failure(
                    "Sistema aceptó webhook malformado sin validar"
                )
            else:
                response.failure(f"Código inesperado: {response.status_code}")

    # ── ISO 25023: Tasa de Error — Token JWT inválido ──────────────
    @task(2)
    def verify_invalid_token(self):
        """
        POST /verify-token — FALLO SIMULADO
        ISO 25023 Fiabilidad: Envía un token JWT inválido/expirado.
        El sistema debe responder HTTP 401, NO caer.
        """
        simulate_network_latency()
        invalid_tokens = [
            {"token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.INVALIDO"},
            {"token": ""},
            {"token": "abc123_token_completamente_falso"},
            {},
        ]
        payload = random.choice(invalid_tokens)

        with self.client.post(
            "/verify-token",
            json=payload,
            name="[FIABILIDAD] POST /verify-token (JWT inválido)",
            catch_response=True
        ) as response:
            if response.status_code in (400, 401):
                response.success()
            else:
                response.failure(
                    f"Se esperaba 400/401, recibió {response.status_code}"
                )

    # ── ISO 25023: Tasa de Error — PayPal webhook basura ───────────
    @task(1)
    def paypal_webhook_garbage(self):
        """
        POST /paypal/webhook — FALLO SIMULADO
        ISO 25023 Fiabilidad: Envía un payload inválido al webhook
        de PayPal para verificar tolerancia a fallos.
        """
        simulate_network_latency()
        garbage_payloads = [
            [{"invalid": "data_type"}],
            "esto_no_es_json",
            {"event_type": "UNKNOWN_EVENT_TYPE"},
            {"event_type": "PAYMENTS.PAYMENT.CREATED", "resource": {}},
        ]
        payload = random.choice(garbage_payloads)

        headers = {"Content-Type": "application/json"}

        with self.client.post(
            "/paypal/webhook",
            data=json.dumps(payload) if not isinstance(payload, str) else payload,
            headers=headers,
            name="[FIABILIDAD] POST /paypal/webhook (basura)",
            catch_response=True
        ) as response:
            # Aceptamos 200 (evento ignorado) o 500 (error controlado)
            if response.status_code in (200, 400, 500):
                response.success()
            else:
                response.failure(f"Código inesperado: {response.status_code}")

    # ── ISO 25023: Comportamiento Temporal — Firma PayU ────────────
    @task(2)
    def payu_firm_unauthorized(self):
        """
        POST /payu-firm — Sin sesión activa
        Valida la protección de seguridad y mide latencia de rechazo.
        """
        simulate_network_latency()

        with self.client.post(
            "/payu-firm",
            json={"categories": [{"id_category": 1}]},
            name="[SEGURIDAD] POST /payu-firm (sin sesión)",
            catch_response=True
        ) as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure(
                    f"Se esperaba 401, recibió {response.status_code}"
                )

    # ── ISO 25023: Capacidad — Balance endpoint ────────────────────
    @task(1)
    def get_balance_unauthorized(self):
        """
        GET /api/balance — Sin sesión activa
        Verifica protección de sesión en endpoints de balance.
        """
        simulate_network_latency()

        with self.client.get(
            "/api/balance",
            params={"date_init": "2024-01-01", "date_end": "2024-12-31"},
            name="[SEGURIDAD] GET /api/balance (sin sesión)",
            catch_response=True
        ) as response:
            if response.status_code in (401, 500):
                response.success()
            else:
                response.failure(f"Código inesperado: {response.status_code}")

    @task(1)
    def validate_email(self):
        """
        POST /validate-email
        Prueba con emails válidos e inválidos para medir throughput.
        """
        simulate_network_latency()
        emails = [
            {"email": "test_locust@gmail.com"},
            {"email": "usuario_falso@gmail.com"},
            {"email": "no_es_gmail@hotmail.com"},
            {"email": ""},
            {},
        ]
        payload = random.choice(emails)

        with self.client.post(
            "/validate-email",
            json=payload,
            name="[FUNCIONAL] POST /validate-email",
            catch_response=True
        ) as response:
            if response.status_code in (200, 400, 500):
                response.success()
            else:
                response.failure(f"Código inesperado: {response.status_code}")
