from flask import Blueprint, request, jsonify
from servises.groups.repository import GroupRepository


class ValidateData:
    def validate_request_data(required_fields):
        data = request.get_json()
        if not data:
            return None, (jsonify({"error": "No se proporcionaron datos"}), 400)
        for field in required_fields:
            if field not in data:
                return None, (jsonify({"error": f"Falta el parámetro: {field}"}), 400)
        return data, None

