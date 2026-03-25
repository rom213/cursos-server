from typing import Any

from fastapi import HTTPException


class ValidateData:
    @staticmethod
    def validate_request_data(required_fields: list[str], data: dict[str, Any] | None):
        if not data:
            raise HTTPException(status_code=400, detail="No se proporcionaron datos")
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Falta el parámetro: {field}")
        return data
