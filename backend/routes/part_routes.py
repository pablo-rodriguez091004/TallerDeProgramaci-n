from flask import Blueprint, request, jsonify
from flask_login import current_user
from db.conexion import db
from models.part_model import Part
from models.business_model import Business
from middlewares.auth_middleware import role_required

part_bp = Blueprint('parts', __name__)


def _current_business():
    if current_user.role == 'owner':
        return Business.query.filter_by(owner_user_id=current_user.user_id).first()
    return Business.query.first()


@part_bp.route('', methods=['GET'])
@role_required('owner', 'admin', 'mechanic')
def list_parts():
    business = _current_business()
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    parts = Part.query.filter_by(business_id=business.business_id, status='active').all()
    return jsonify([_serialize_part(p) for p in parts]), 200


@part_bp.route('', methods=['POST'])
@role_required('owner', 'admin')
def create_part():
    business = _current_business()
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    data = request.get_json()
    required_fields = ['part_name', 'unit_price']
    for field in required_fields:
        if field not in data or data[field] in (None, ''):
            return jsonify({'error': f'El campo {field} es obligatorio'}), 400

    part = Part(
        business_id=business.business_id,
        part_name=data['part_name'],
        unit_price=data['unit_price'],
        stock_quantity=data.get('stock_quantity', 0)
    )
    db.session.add(part)
    db.session.commit()

    return jsonify({'message': 'Repuesto creado', 'part_id': part.part_id}), 201


@part_bp.route('/<int:part_id>', methods=['PUT'])
@role_required('owner', 'admin')
def update_part(part_id):
    part = Part.query.get(part_id)
    if not part:
        return jsonify({'error': 'Repuesto no encontrado'}), 404

    data = request.get_json()
    editable_fields = ['part_name', 'unit_price', 'stock_quantity', 'status']
    for field in editable_fields:
        if field in data:
            setattr(part, field, data[field])

    db.session.commit()
    return jsonify({'message': 'Repuesto actualizado'}), 200


def _serialize_part(p):
    return {
        'part_id': p.part_id,
        'part_name': p.part_name,
        'unit_price': p.unit_price,
        'stock_quantity': p.stock_quantity,
        'status': p.status
    }
