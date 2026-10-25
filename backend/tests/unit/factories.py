"""
Fabricas de entidades y actores para las pruebas unitarias.

Los puertos se simulan con unittest.mock.create_autospec(Puerto, instance=True):
el mock solo acepta los metodos y firmas que declara el puerto, asi una
prueba falla si el servicio usa algo que la interfaz no ofrece.
"""

from datetime import datetime

from domain.catalog.entities import Bay, Part, Service, Vehicle
from domain.identity.entities import User
from domain.payments.entities import Payment
from domain.scheduling.entities import Appointment
from domain.shared.actor import Actor

CLIENT = Actor(user_id=3, role='client')
OTHER_CLIENT = Actor(user_id=99, role='client')
MECHANIC = Actor(user_id=2, role='mechanic')
OWNER = Actor(user_id=1, role='owner')
ADMIN = Actor(user_id=4, role='admin')
START = datetime(2030, 1, 10, 9, 0)


def make_vehicle(**overrides):
    return Vehicle(**{'vehicle_id': 10, 'owner_user_id': CLIENT.user_id, 'license_plate': 'ABC123', 'brand': 'Mazda',
                      'model': '3', 'year': 2020, 'vehicle_type': 'car', 'fuel_type': 'gasoline',
                      'transmission_type': 'automatic', **overrides})


def make_service(**overrides):
    return Service(**{'service_id': 1, 'business_id': 1, 'service_name': 'Cambio de aceite',
                      'estimated_duration_minutes': 45, 'base_price': 80000, **overrides})


def make_bay(**overrides):
    return Bay(**{'bay_id': 1, 'business_id': 1, 'bay_number': 'Bahia 1', **overrides})


def make_mechanic(**overrides):
    return User(**{'user_id': MECHANIC.user_id, 'first_name': 'Andres', 'last_name': 'Test', 'document_number': '1002',
                   'email': 'mechanic@test.com', 'role': 'mechanic', 'password_hash': 'x', **overrides})


def make_appointment(**overrides):
    return Appointment(**{'appointment_id': 7, 'client_user_id': CLIENT.user_id, 'vehicle_id': 10, 'service_id': 1,
                          'bay_id': 1, 'mechanic_user_id': MECHANIC.user_id, 'scheduled_start': START,
                          'scheduled_end': datetime(2030, 1, 10, 9, 45), 'status': 'pending', **overrides})


def make_payment(**overrides):
    return Payment(**{'payment_id': 21, 'appointment_id': 7, 'payment_type': 'deposit', 'payment_method': 'cash',
                      'amount': 24000, **overrides})


def make_part(**overrides):
    return Part(**{'part_id': 5, 'business_id': 1, 'part_name': 'Aceite 5W30', 'unit_price': 40000,
                   'stock_quantity': 5, **overrides})
