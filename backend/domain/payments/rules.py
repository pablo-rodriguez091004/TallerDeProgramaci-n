"""Reglas de los pagos simulados: deposito + saldo."""

# Porcentaje del precio del servicio que se cobra como deposito inicial.
# Valor de ejemplo, ajustable segun la regla de negocio real del taller.
DEPOSIT_PERCENTAGE = 0.3


def split_price(base_price, deposit_percentage=DEPOSIT_PERCENTAGE):
    """
    Devuelve (deposito, saldo). El saldo se calcula como resta para que la
    suma sea exactamente el precio aunque el deposito se redondee.
    """
    deposit = round(base_price * deposit_percentage)
    return deposit, base_price - deposit


def confirms_appointment(payment, appointment):
    """Pagar el DEPOSITO de una cita pendiente es lo que la confirma."""
    return payment.is_deposit and appointment.status == 'pending'
