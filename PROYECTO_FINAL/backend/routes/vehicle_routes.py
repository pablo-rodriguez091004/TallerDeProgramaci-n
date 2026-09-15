from flask import Blueprint, request, jsonify
from flask_login import current_user
from db.conexion import db
from models.vehicle_model import Vehicle
from middlewares.auth_middleware import role_required

vehicle_bp = Blueprint('vehicles', __name__)


@vehicle_bp.route('', methods=['POST'])
@role_required('client')
def create_vehicle():
    data = request.get_json()

    required_fields = ['license_plate', 'brand', 'model', 'year', 'vehicle_type', 'fuel_type', 'transmission_type']
    for field in required_fields:
        if field not in data or data[field] in (None, ''):
            return jsonify({'error': f'El campo {field} es obligatorio'}), 400

    if Vehicle.query.filter_by(license_plate=data['license_plate']).first():
        return jsonify({'error': 'Esa placa ya está registrada'}), 409

    vehicle = Vehicle(
        owner_user_id=current_user.user_id,
        license_plate=data['license_plate'],
        brand=data['brand'],
        model=data['model'],
        year=data['year'],
        color=data.get('color'),
        vehicle_type=data['vehicle_type'],
        vin=data.get('vin'),
        engine_displacement=data.get('engine_displacement'),
        mileage=data.get('mileage'),
        fuel_type=data['fuel_type'],
        transmission_type=data['transmission_type']
    )

    db.session.add(vehicle)
    db.session.commit()

    return jsonify({'message': 'Vehículo registrado', 'vehicle_id': vehicle.vehicle_id}), 201


@vehicle_bp.route('', methods=['GET'])
@role_required('client')
def list_my_vehicles():
    vehicles = Vehicle.query.filter_by(owner_user_id=current_user.user_id).all()
    return jsonify([_serialize_vehicle(v) for v in vehicles]), 200


@vehicle_bp.route('/<int:vehicle_id>', methods=['GET'])
@role_required('client', 'mechanic', 'admin', 'owner')
def get_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehículo no encontrado'}), 404

    if current_user.role == 'client' and vehicle.owner_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para ver este vehículo'}), 403

    return jsonify(_serialize_vehicle(vehicle)), 200


@vehicle_bp.route('/<int:vehicle_id>', methods=['PUT'])
@role_required('client')
def update_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehículo no encontrado'}), 404
    if vehicle.owner_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para editar este vehículo'}), 403

    data = request.get_json()
    editable_fields = ['brand', 'model', 'year', 'color', 'vehicle_type', 'mileage', 'fuel_type', 'transmission_type']
    for field in editable_fields:
        if field in data:
            setattr(vehicle, field, data[field])

    db.session.commit()
    return jsonify({'message': 'Vehículo actualizado'}), 200


@vehicle_bp.route('/<int:vehicle_id>', methods=['DELETE'])
@role_required('client')
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehículo no encontrado'}), 404
    if vehicle.owner_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para eliminar este vehículo'}), 403

    db.session.delete(vehicle)
    db.session.commit()
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
