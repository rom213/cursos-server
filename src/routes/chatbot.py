from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
import uuid
from datetime import datetime
from database import get_db

router = APIRouter(tags=["chatbot"])

# URL del webhook n8n
N8N_WEBHOOK_URL = "https://personal-n8n.85wqxz.easypanel.host/webhook/46c87db9-da2e-4c79-9f26-f77bd4d86be6"

# Mock responses para testing (quitar cuando n8n funcione)
MOCK_RESPONSES = {
    "hola": "¡Hola! Bienvenido a nuestros cursos. ¿En qué puedo ayudarte?",
    "ayuda": "Estoy aquí para ayudarte con:\n- Información sobre cursos\n- Acceso a materiales\n- Preguntas frecuentes\n\n¿Qué necesitas?",
    "cursos": "Tenemos tres categorías principales:\n- **Imperio Comercial** - Trading, bienes raíces, marketing\n- **Ingeniería y Tecnología** - Programación, IA, DevOps\n- **Academia Creativa** - Diseño, video, música, fitness\n\n¿Cuál te interesa?",
    "default": "Entiendo. Te puedo ayudar con información sobre nuestros cursos. ¿Hay algo específico que quieras saber?"
}


@router.post("/chatbot/message")
def send_message(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Envía un mensaje al chatbot (Clarita) a través del webhook n8n

    Expected payload:
    {
        "message": "texto del usuario",
        "user_email": "email@example.com",
        "user_name": "Nombre Usuario",
        "user_photo": "https://..."
    }
    """
    try:
        message = body.get("message", "").strip()
        user_email = body.get("user_email", "")
        user_name = body.get("user_name", "")
        user_photo = body.get("user_photo", "")

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        if not user_email:
            raise HTTPException(status_code=400, detail="User email is required")

        # Construir payload para n8n con la misma estructura esperada
        payload = {
            "instancia": {
                "nombre": "Web_Chat",
                "apikey": "none",
                "server_url": "web"
            },
            "message": {
                "id": str(uuid.uuid4()),
                "chat_id": user_email,
                "username": user_name,
                "content": message,
                "content_type": "texto",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        print(f"[CHATBOT] Mensaje de {user_email}: {message[:50]}...")

        # Intentar conectar a n8n
        try:
            print(f"[CHATBOT] Intentando conectar a n8n: {N8N_WEBHOOK_URL}")
            response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)

            print(f"[CHATBOT] n8n response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                output = data.get("output", "")

                if output:
                    print(f"[CHATBOT] Response from n8n: OK")
                    return {
                        "success": True,
                        "output": output
                    }

        except requests.Timeout:
            print(f"[CHATBOT] n8n timeout - usando respuesta mock")
        except requests.RequestException as e:
            print(f"[CHATBOT] n8n error: {e} - usando respuesta mock")
        except Exception as e:
            print(f"[CHATBOT] Unexpected error: {e} - usando respuesta mock")

        # Fallback: usar respuestas mock
        print(f"[CHATBOT] Usando respuesta mock para: {message[:30]}")
        message_lower = message.lower()

        # Buscar respuesta en las palabras clave
        output = MOCK_RESPONSES.get("default")
        for key, response_text in MOCK_RESPONSES.items():
            if key != "default" and key in message_lower:
                output = response_text
                break

        return {
            "success": True,
            "output": output,
            "source": "mock"  # Para indicar que es una respuesta temporal
        }

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Chatbot service timeout")
    except requests.RequestException as e:
        print(f"[CHATBOT ERROR] {e}")
        raise HTTPException(status_code=502, detail="Chatbot service unavailable")
    except Exception as e:
        print(f"[CHATBOT ERROR] {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/chatbot/reset")
def reset_conversation(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Reinicia la conversación y borra la memoria de Clarita

    Expected payload:
    {
        "user_email": "email@example.com"
    }
    """
    try:
        user_email = body.get("user_email", "")

        if not user_email:
            raise HTTPException(status_code=400, detail="User email is required")

        print(f"[CHATBOT] Reseteando conversación para {user_email}")

        # Intentar enviar reset al webhook n8n
        try:
            reset_payload = {
                "action": "reset_memory",
                "userId": user_email
            }
            response = requests.post(N8N_WEBHOOK_URL, json=reset_payload, timeout=5)
            print(f"[CHATBOT] Reset enviado a n8n: {response.status_code}")
        except Exception as e:
            print(f"[CHATBOT] No se pudo conectar a n8n para reset: {e}")

        # El reset visual ya ocurrió en el cliente
        return {
            "success": True,
            "message": "Conversación reiniciada"
        }

    except Exception as e:
        print(f"[CHATBOT RESET ERROR] {e}")
        return {
            "success": True,
            "message": "Conversación reiniciada"
        }
