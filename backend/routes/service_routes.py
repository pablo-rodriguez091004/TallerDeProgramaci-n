from flask import Blueprint, request, jsonify
from flask_login import current_user
from db.conexion import db
from models.service_model import Service
from models.business_model import Business
from middlewares.auth_middleware import role_required

service_bp = Blueprint('services', __name__)


def _current_business():
    """
    Devuelve el negocio sobre el que opera el usuario actual.
    El 'owner' tiene su propio negocio via owner_user_id.
    El 'admin' no tiene ese vinculo directo en el esquema actual, asi que
    (dado que hoy solo existe un negocio en el sistema) se le asigna el
    primero que exista. Si el proyecto llega a soportar varios negocios,
    hay que agregar una relacion explicita admin->negocio.
    """
    if current_user.role == 'owner':
        return Business.query.filter_by(owner_user_id=current_user.user_id).first()
    return Business.query.first()


@service_bp.route('', methods=['GET'])
def list_services():
    services = Service.query.filter_by(status='active').all()
    return jsonify([_serialize_service(s) for s in services]), 200


@service_bp.route('', methods=['POST'])
@role_required('owner', 'admin')
def create_service():
    business = _current_business()
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    data = request.get_json()
    required_fields = ['service_name', 'estimated_duration_minutes', 'base_price']
    for field in required_fields:
        if field not in data or data[field] in (None, ''):
            return jsonify({'error': f'El campo {field} es obligatorio'}), 400

    service = Service(
        business_id=business.business_id,
        service_name=data['service_name'],
        description=data.get('description'),
        estimated_duration_minutes=data['estimated_duration_minutes'],
        base_price=data['base_price']
    )
    db.session.add(service)
    db.session.commit()

    return jsonify({'message': 'Servicio creado', 'service_id': service.service_id}), 201


@service_bp.route('/<int:service_id>', methods=['PUT'])
@role_required('owner', 'admin')
def update_service(service_id):
    service = Service.query.get(service_id)
    if not service:
        return jsonify({'error': 'Servicio no encontrado'}), 404

    data = request.get_json()
    editable_fields = ['service_name', 'description', 'estimated_duration_minutes', 'base_price', 'status']
    for field in editable_fields:
        if field in data:
            setattr(service, field, data[field])

    db.session.commit()
    return jsonify({'message': 'Servicio actualizado'}), 200


@service_bp.route('/<int:service_id>', methods=['DELETE'])
@role_required('owner', 'admin')
def deactivate_service(service_id):
    """
    No se borra fisicamente el servicio (podria tener citas historicas
    asociadas por FK) - se desactiva marcando status='inactive'.
    """
    service = Service.query.get(service_id)
    if not service:
        return jsonify({'error': 'Servicio no encontrado'}), 404

    service.status = 'inactive'
    db.session.commit()
    return jsonify({'message': 'Servicio desactivado'}), 200


def _serialize_service(s):
    return {
        'service_id': s.service_id,
        'service_name': s.service_name,
        'description': s.description,
        'estimated_duration_minutes': s.estimated_duration_minutes,
        'base_price': s.base_price,
        'status': s.status
    }
