"""Rutas antiguas que consume el frontend. Errores con formato {"error": "..."}."""

from flask import jsonify, request


def json_body():
    return request.get_json(silent=True) or {}


def missing_field(data, required, allow_falsy=False):
    """
    Devuelve la respuesta 400 del primer campo obligatorio ausente, o None.
    allow_falsy=True acepta 0/False (solo rechaza None y '').
    """
    for field in required:
        value = data.get(field)
        empty = value in (None, '') if allow_falsy else not value
        if field not in data or empty:
            return jsonify({'error': f'El campo {field} es obligatorio'}), 400
    return None
