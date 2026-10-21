from datetime import datetime

from db.conexion import db


class AiCall(db.Model):
    """
    Bitacora de cada llamada al LLM (exitosa o fallida): sirve para auditar,
    para el limite de llamadas por usuario y como evidencia de la Guia 5.
    """
    __tablename__ = 'ai_calls'

    ai_call_id = db.Column(db.Integer, primary_key=True)
    # Nulo cuando la llamada la hace un script (p. ej. la evaluacion de prompts).
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    source = db.Column(db.String(20), nullable=False, default='api', server_default='api')
    technique = db.Column(db.String(20), nullable=False)
    model = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    input_tokens = db.Column(db.Integer, nullable=True)
    output_tokens = db.Column(db.Integer, nullable=True)
    # Gemini factura los tokens de "thinking" como salida: se guardan aparte.
    thinking_tokens = db.Column(db.Integer, nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    attempts = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    status = db.Column(db.String(20), nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           server_default=db.func.current_timestamp())

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('success', 'timeout', 'rate_limited', 'provider_error', 'invalid_response', 'not_configured')",
            name='check_ai_call_status'
        ),
        db.CheckConstraint("technique IN ('zero_shot', 'few_shot', 'cot')", name='check_ai_call_technique'),
        # Limite por usuario: cuenta las llamadas de la ultima hora.
        db.Index('ix_ai_calls_user_created', 'user_id', 'created_at'),
    )
