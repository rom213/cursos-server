"""
Compatibilidad: la verificación de sesión Flask se sustituye por JWT en rutas FastAPI.
"""
from utils.auth import get_token_payload_optional

# Re-export para imports existentes que esperen UserRepository.verify_seccion
class UserRepository:
    @staticmethod
    def verify_seccion():
        """Obsoleto: usar Depends(get_current_user_payload)."""
        return False
