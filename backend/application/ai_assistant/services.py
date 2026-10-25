"""
Caso de uso: el cliente describe un sintoma y el sistema sugiere servicios
del catalogo con precio y duracion.

Flujo (RAG):
  descripcion -> retrieval.retrieve() -> prompts.build_prompt() ->
  LlmGateway.generate() -> validar JSON -> enriquecer con el catalogo -> AiCallLog

Cada llamada al proveedor queda registrada en la bitacora, tambien las
fallidas. Lo usan el endpoint y scripts/run_prompt_eval.py (source='eval').
"""

from datetime import timedelta

from domain.ai_assistant import prompts, retrieval
from domain.ai_assistant.answer import parse_model_answer
from domain.ai_assistant.errors import InvalidModelResponse, LlmError, UserQuotaExceeded
from domain.ai_assistant.ports import AiCallLog, LlmGateway
from domain.catalog.ports import ServiceRepository
from domain.shared.ports import Clock


class AiAssistantService:

    def __init__(self, services: ServiceRepository, llm: LlmGateway, call_log: AiCallLog, clock: Clock):
        self._services = services
        self._llm = llm
        self._call_log = call_log
        self._clock = clock

    def check_user_quota(self, user_id, limit):
        """Limite propio por usuario (cuida la cuota gratuita del proveedor)."""
        now = self._clock.now()
        count, oldest = self._call_log.api_calls_since(user_id, now - timedelta(hours=1))
        if count >= limit:
            retry_after = max(1, int((oldest + timedelta(hours=1) - now).total_seconds()))
            raise UserQuotaExceeded(limit, retry_after)

    def retrieve(self, description):
        return retrieval.retrieve(description, self._services.list_active())

    def suggest_services(self, description, technique=prompts.DEFAULT_TECHNIQUE, user_id=None, source='api'):
        """
        Ejecuta el flujo completo. Devuelve el dict de la respuesta o lanza
        LlmError / InvalidModelResponse (ya registradas en la bitacora).
        """
        context = self.retrieve(description)
        services = context['services']
        system_prompt, user_prompt = prompts.build_prompt(technique, description, services)
        full_prompt = f'[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}'
        base_log = {'user_id': user_id, 'source': source, 'technique': technique,
                    'description': description, 'prompt': full_prompt}

        try:
            result = self._llm.generate(system_prompt, user_prompt)
        except LlmError as exc:
            exc.ai_call_id = self._call_log.record(**base_log, status=exc.status, error_message=str(exc),
                                                   attempts=exc.attempts, latency_ms=exc.latency_ms)
            raise

        usage_log = {'model': result.model, 'response': result.text, 'input_tokens': result.input_tokens,
                     'output_tokens': result.output_tokens, 'thinking_tokens': result.thinking_tokens,
                     'latency_ms': result.latency_ms, 'attempts': result.attempts}
        by_id = {s.service_id: s for s in services}
        try:
            suggestions, notes, reasoning, discarded = parse_model_answer(result.text, set(by_id))
        except InvalidModelResponse as exc:
            exc.ai_call_id = self._call_log.record(**base_log, **usage_log, status='invalid_response',
                                                   error_message=str(exc))
            raise

        ai_call_id = self._call_log.record(**base_log, **usage_log, status='success')

        # Nombre, precio y duracion salen del catalogo, nunca del texto del modelo.
        enriched = [{
            'service_id': item['service_id'],
            'service_name': by_id[item['service_id']].service_name,
            'base_price': by_id[item['service_id']].base_price,
            'estimated_duration_minutes': by_id[item['service_id']].estimated_duration_minutes,
            'confidence': item['confidence'],
            'reason': item['reason'],
        } for item in suggestions]

        return {
            'ai_call_id': ai_call_id,
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
