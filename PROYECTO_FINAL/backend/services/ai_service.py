"""
Caso de uso: el cliente describe un sintoma y el sistema sugiere servicios
del catalogo con precio y duracion.

Flujo (RAG):
  descripcion -> retrieval.retrieve() -> prompts.build_prompt() ->
  llm_client.generate() -> validar JSON -> enriquecer con la BD -> ai_calls

Cada llamada al proveedor queda registrada en ai_calls, tambien las fallidas.
La usan tanto el endpoint como scripts/run_prompt_eval.py (source='eval').
"""

import json
import re
from datetime import datetime, timedelta

from db.conexion import db
from models.ai_call_model import AiCall
from repositories import service_repository
from services import llm_client, prompts, retrieval

CONFIDENCE_LEVELS = ('high', 'medium', 'low')


class InvalidModelResponse(Exception):
    pass


class UserQuotaExceeded(Exception):
    def __init__(self, limit, retry_after_s):
        super().__init__(f'Limit of {limit} AI calls per hour reached')
        self.limit = limit
        self.retry_after_s = retry_after_s


def check_user_quota(user_id, limit):
    """Limite propio por usuario (cuida la cuota gratuita del proveedor)."""
    window_start = datetime.utcnow() - timedelta(hours=1)
    calls = (AiCall.query
             .filter(AiCall.user_id == user_id, AiCall.source == 'api', AiCall.created_at >= window_start)
             .order_by(AiCall.created_at))
    if calls.count() >= limit:
        oldest = calls.first().created_at
        retry_after = max(1, int((oldest + timedelta(hours=1) - datetime.utcnow()).total_seconds()))
        raise UserQuotaExceeded(limit, retry_after)


def parse_model_answer(text, allowed_ids):
    """
    Valida el JSON del modelo. Devuelve (sugerencias, notes, reasoning, descartados).
    Los service_id que no estaban en el contexto se descartan: es la defensa
    contra servicios inventados (alucinaciones).
    """
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise InvalidModelResponse(f'The model did not return valid JSON: {exc.msg}') from exc
    if not isinstance(data, dict) or not isinstance(data.get('suggestions'), list):
        raise InvalidModelResponse('The model JSON has no "suggestions" list')

    suggestions, discarded, seen = [], [], set()
    for item in data['suggestions']:
        if not isinstance(item, dict):
            continue
        service_id = item.get('service_id')
        if not isinstance(service_id, int) or service_id not in allowed_ids:
            discarded.append(service_id)
            continue
        if service_id in seen:
            continue
        seen.add(service_id)
        confidence = item.get('confidence') if item.get('confidence') in CONFIDENCE_LEVELS else 'low'
        suggestions.append({'service_id': service_id, 'confidence': confidence,
                            'reason': str(item.get('reason') or '').strip()})

    notes = str(data.get('notes') or '').strip()
    reasoning = data.get('reasoning')
    return suggestions[:prompts.MAX_SUGGESTIONS], notes, reasoning, discarded


def _log_call(**fields):
    call = AiCall(**fields)
    db.session.add(call)
    db.session.commit()
    return call


def suggest_services(description, technique=prompts.DEFAULT_TECHNIQUE, user_id=None, source='api'):
    """
    Ejecuta el flujo completo. Devuelve el dict de la respuesta o lanza
    llm_client.LlmError / InvalidModelResponse (ya registradas en ai_calls).
    """
    context = retrieval.retrieve(description)
    services = context['services']
    system_prompt, user_prompt = prompts.build_prompt(technique, description, services)
    full_prompt = f'[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}'
    base_log = {'user_id': user_id, 'source': source, 'technique': technique,
                'description': description, 'prompt': full_prompt}

    try:
        result = llm_client.generate(system_prompt, user_prompt)
    except llm_client.LlmError as exc:
        call = _log_call(**base_log, status=exc.status, error_message=str(exc), attempts=exc.attempts,
                         latency_ms=exc.latency_ms)
        exc.ai_call_id = call.ai_call_id  # para que el cliente pueda rastrear el fallo
        raise

    usage_log = {'model': result.model, 'response': result.text, 'input_tokens': result.input_tokens,
                 'output_tokens': result.output_tokens, 'thinking_tokens': result.thinking_tokens,
                 'latency_ms': result.latency_ms, 'attempts': result.attempts}
    try:
        suggestions, notes, reasoning, discarded = parse_model_answer(
            result.text, {s.service_id for s in services})
    except InvalidModelResponse as exc:
        call = _log_call(**base_log, **usage_log, status='invalid_response', error_message=str(exc))
        exc.ai_call_id = call.ai_call_id
        raise

    call = _log_call(**base_log, **usage_log, status='success')

    # Nombre, precio y duracion salen de la BD, nunca del texto del modelo.
    enriched = []
    for item in suggestions:
        service = service_repository.get_by_id(item['service_id'])
        enriched.append({
            'service_id': service.service_id,
            'service_name': service.service_name,
            'base_price': service.base_price,
            'estimated_duration_minutes': service.estimated_duration_minutes,
            'confidence': item['confidence'],
            'reason': item['reason'],
        })

    return {
        'ai_call_id': call.ai_call_id,
        'technique': technique,
        'model': result.model,
        'suggestions': enriched,
        'notes': notes,
        'reasoning': reasoning if isinstance(reasoning, str) else None,
        'discarded_service_ids': discarded,
        'retrieval': {
            'strategy': 'keyword',
            'fallback_full_catalog': context['fallback'],
            'candidate_service_ids': [s.service_id for s in services],
        },
        'usage': {
            'input_tokens': result.input_tokens,
            'output_tokens': result.output_tokens,
            'thinking_tokens': result.thinking_tokens,
            'latency_ms': result.latency_ms,
            'attempts': result.attempts,
        },
    }
