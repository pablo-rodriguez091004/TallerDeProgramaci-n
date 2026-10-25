from flask import Blueprint, jsonify

from api.auth import role_required
from api.deps import actor, container
from api.legacy import json_body, missing_field

vehicle_bp = Blueprint('vehicles', __name__)

REQUIRED_FIELDS = ['license_plate', 'brand', 'model', 'year', 'vehicle_type', 'fuel_type', 'transmission_type']


@vehicle_bp.route('', methods=['POST'])
@role_required('client')
def create_vehicle():
    data = json_body()
    error = missing_field(data, REQUIRED_FIELDS, allow_falsy=True)
    if error:
        return error
    vehicle = container().vehicles.register(actor(), data)
    return jsonify({'message': 'Vehículo registrado', 'vehicle_id': vehicle.vehicle_id}), 201


@vehicle_bp.route('', methods=['GET'])
@role_required('client')
def list_my_vehicles():
    return jsonify([_serialize_vehicle(v) for v in container().vehicles.list_mine(actor())]), 200


@vehicle_bp.route('/<int:vehicle_id>', methods=['GET'])
@role_required('client', 'mechanic', 'admin', 'owner')
def get_vehicle(vehicle_id):
    return jsonify(_serialize_vehicle(container().vehicles.get(actor(), vehicle_id))), 200


@vehicle_bp.route('/<int:vehicle_id>', methods=['PUT'])
@role_required('client')
def update_vehicle(vehicle_id):
    container().vehicles.update(actor(), vehicle_id, json_body())
    return jsonify({'message': 'Vehículo actualizado'}), 200


@vehicle_bp.route('/<int:vehicle_id>', methods=['DELETE'])
@role_required('client')
def delete_vehicle(vehicle_id):
    container().vehicles.delete(actor(), vehicle_id)
    return jsonify({'message': 'Vehículo eliminado'}), 200


def _serialize_vehicle(v):
    return {
        'vehicle_id': v.vehicle_id,
        'license_plate': v.license_plate,
        'brand': v.brand,
        'model': v.model,
        'year': v.year,
        'color': v.color,
        'vehicle_type': v.vehicle_type,
        'vin': v.vin,
        'engine_displacement': float(v.engine_displacement) if v.engine_displacement is not None else None,
        'mileage': v.mileage,
        'fuel_type': v.fuel_type,
        'transmission_type': v.transmission_type
    }
