from models.business_model import Business


def get_by_owner(owner_user_id):
    return Business.query.filter_by(owner_user_id=owner_user_id).first()


def get_for_user(user):
    """
    Devuelve el negocio sobre el que opera el usuario actual.
    El 'owner' tiene su propio negocio via owner_user_id.
    El 'admin' y el 'mechanic' no tienen ese vinculo directo en el esquema
    actual, asi que (dado que hoy solo existe un negocio en el sistema) se
    les asigna el primero que exista. Si el proyecto llega a soportar varios
    negocios, hay que agregar una relacion explicita usuario->negocio.
    """
    if user.role == 'owner':
        return get_by_owner(user.user_id)
    return Business.query.order_by(Business.business_id).first()
