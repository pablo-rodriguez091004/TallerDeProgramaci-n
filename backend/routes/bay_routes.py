from flask import Blueprint, request, jsonify
from flask_login import current_user
from db.conexion import db
from models.bay_model import Bay
from models.business_model import Business
from middlewares.auth_middleware import role_required

bay_bp = Blueprint('bays', __name__)


def _current_business():
    if current_user.role == 'owner':
        return Business.query.filter_by(owner_user_id=current_user.user_id).first()
    return Business.query.first()


@bay_bp.route('', methods=['GET'])
@role_required('owner', 'admin', 'mechanic')
def list_bays():
    business = _current_business()
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    bays = Bay.query.filter_by(business_id=business.business_id).all()
    return jsonify([_serialize_bay(b) for b in bays]), 200


@bay_bp.route('', methods=['POST'])
@role_required('owner', 'admin')
def create_bay():
    business = _current_business()
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    data = request.get_json()
    if 'bay_number' not in data or not data['bay_number']:
        return jsonify({'error': 'El campo bay_number es obligatorio'}), 400

    if Bay.query.filter_by(business_id=business.business_id, bay_number=data['bay_number']).first():
        return jsonify({'error': 'Ya existe una bahía con ese número en este negocio'}), 409

    bay = Bay(
        business_id=business.business_id,
        bay_number=data['bay_number'],
        has_elevator=data.get('has_elevator', False)
    )
    db.session.add(bay)
    db.session.commit()

    return jsonify({'message': 'Bahía creada', 'bay_id': bay.bay_id}), 201


@bay_bp.route('/<int:bay_id>', methods=['PUT'])
@role_required('owner', 'admin')
def update_bay(bay_id):
    bay = Bay.query.get(bay_id)
    if not bay:
        return jsonify({'error': 'Bahía no encontrada'}), 404

    data = request.get_json()
    if 'has_elevator' in data:
        bay.has_elevator = data['has_elevator']
    if 'status' in data:
        bay.status = data['status']

    db.session.commit()
    return jsonify({'message': 'Bahía actualizada'}), 200


def _serialize_bay(b):
    return {
        'bay_id': b.bay_id,
        'bay_number': b.bay_number,
        'has_elevator': b.has_elevator,
        'status': b.status
    }
