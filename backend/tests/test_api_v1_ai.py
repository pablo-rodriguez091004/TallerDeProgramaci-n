"""
Pruebas de POST /api/v1/ai/suggest-service con el LLM simulado.

Se reemplaza solo gemini_gateway._call_model (la funcion que usa la red): la
recuperacion, los prompts, los reintentos, el mapeo de errores y la bitacora
ai_calls se ejecutan de verdad contra PostgreSQL.
"""

import json
from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors as genai_errors

from domain.ai_assistant import prompts
from infrastructure.llm import gemini_gateway
from infrastructure.persistence.extensions import db
from infrastructure.persistence.models import AiCall

URL = '/api/v1/ai/suggest-service'
SYMPTOM = 'El carro vibra mucho cuando freno en bajada'


def fake_response(payload, input_tokens=420, output_tokens=60, thinking_tokens=None):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    usage = SimpleNamespace(prompt_token_count=input_tokens, candidates_token_count=output_tokens,
                            thoughts_token_count=thinking_tokens)
    return SimpleNamespace(text=text, usage_metadata=usage, model_version='test-model-001')


def api_error(code):
    return genai_errors.ClientError(code, {'error': {'code': code, 'message': 'simulated', 'status': 'X'}})


class FakeModel:
    """Sustituto de _call_model: devuelve/lanza en orden lo que se le indique."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, api_key, model, system_prompt, user_prompt, timeout_s, temperature):
        self.calls.append({'model': model, 'system': system_prompt, 'user': user_prompt, 'timeout_s': timeout_s})
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture
def brake_catalog(app):
    """Agrega al seed (1 = Cambio de aceite) servicios de frenos y bateria."""
    from infrastructure.persistence.models import Service
    with app.app_context():
        db.session.add_all([
            Service(business_id=1, service_name='Cambio de pastillas de freno',
                    description='Reemplazo de pastillas de freno', estimated_duration_minutes=90, base_price=180000),
            Service(business_id=1, service_name='Rectificación de discos de freno',
                    description='Rectificado de discos alabeados que causan vibracion al frenar',
                    estimated_duration_minutes=120, base_price=220000),
            Service(business_id=1, service_name='Revisión de batería',
                    description='Prueba de bateria y alternador', estimated_duration_minutes=60, base_price=100000),
        ])
        db.session.commit()


@pytest.fixture
def fake_model(monkeypatch):
    def _install(*outcomes):
        model = FakeModel(*outcomes)
        monkeypatch.setattr(gemini_gateway, '_call_model', model)
        return model
    return _install


def _ai_calls(app):
    with app.app_context():
        return AiCall.query.order_by(AiCall.ai_call_id).all()


def _assert_error(response, status, code):
    assert response.status_code == status, response.get_json()
    body = response.get_json()
    assert set(body) == {'code', 'message', 'details'} and body['code'] == code
    return body


# --- Exito -------------------------------------------------------------------

def test_success_uses_rag_context_and_prices_from_database(app, login, brake_catalog, fake_model):
    model = fake_model(fake_response({
        'suggestions': [
            {'service_id': 3, 'confidence': 'high', 'reason': 'Discos alabeados.'},
            {'service_id': 2, 'confidence': 'medium', 'reason': 'Pastillas gastadas.', 'base_price': 1},
            {'service_id': 999, 'confidence': 'high', 'reason': 'Servicio inventado.'},
        ],
        'notes': 'Riesgo de seguridad.'}))
    client = login('client@test.com')

    response = client.post(URL, json={'description': SYMPTOM})
    assert response.status_code == 200, response.get_json()
    body = response.get_json()

    # Contexto RAG: los servicios de frenos, el de mayor puntaje primero; no la bateria
    assert body['retrieval']['candidate_service_ids'][:2] == [3, 2]
    assert 4 not in body['retrieval']['candidate_service_ids']
    assert '[3] Rectificación de discos de freno' in model.calls[0]['user']
    assert model.calls[0]['model'] == 'test-model'

    # Precio/duracion salen de la BD (el 'base_price': 1 del modelo se ignora)
    # y el id inventado (999) se descarta
    assert [(s['service_id'], s['base_price'], s['estimated_duration_minutes']) for s in body['suggestions']] == [
        (3, 220000, 120), (2, 180000, 90)]
    assert body['discarded_service_ids'] == [999]
    assert body['technique'] == 'few_shot' and body['reasoning'] is None
    assert body['usage'] == {'input_tokens': 420, 'output_tokens': 60, 'thinking_tokens': 0,
                             'latency_ms': body['usage']['latency_ms'], 'attempts': 1}

    [call] = _ai_calls(app)
    assert (call.ai_call_id, call.user_id, call.status, call.technique) == (body['ai_call_id'], 3, 'success', 'few_shot')
    assert (call.input_tokens, call.output_tokens, call.model) == (420, 60, 'test-model-001')
    assert call.prompt.startswith('[SYSTEM]') and 'Example 1' in call.prompt and SYMPTOM in call.prompt
    assert json.loads(call.response)['notes'] == 'Riesgo de seguridad.'


def test_cot_technique_returns_reasoning(login, brake_catalog, fake_model):
    model = fake_model(fake_response({'reasoning': '1) Frenos. 2) Discos. 3) Rectificar.',
                                      'suggestions': [{'service_id': 3, 'confidence': 'high', 'reason': 'x'}],
                                      'notes': ''}))
    body = login('client@test.com').post(URL, json={'description': SYMPTOM, 'technique': 'cot'}).get_json()
    assert body['reasoning'].startswith('1) Frenos')
    assert 'Think step by step' in model.calls[0]['user'] and 'Example 1' not in model.calls[0]['user']


# --- Errores del proveedor -----------------------------------------------------

def test_timeout_returns_504_and_is_logged(app, login, fake_model):
    fake_model(httpx.ReadTimeout('timed out'))
    body = _assert_error(login('client@test.com').post(URL, json={'description': SYMPTOM}), 504, 'llm_timeout')

    [call] = _ai_calls(app)
    assert call.status == 'timeout' and call.response is None
    assert body['details'] == {'ai_call_id': call.ai_call_id, 'attempts': 1}


def test_rate_limit_is_retried_with_backoff_then_succeeds(app, login, brake_catalog, fake_model):
    model = fake_model(api_error(429), api_error(429),
                       fake_response({'suggestions': [{'service_id': 3, 'confidence': 'high', 'reason': 'x'}]}))
    response = login('client@test.com').post(URL, json={'description': SYMPTOM})
    assert response.status_code == 200, response.get_json()
    assert response.get_json()['usage']['attempts'] == 3 and len(model.calls) == 3


def test_rate_limit_after_all_retries_returns_429(app, login, fake_model):
    model = fake_model(api_error(429))
    body = _assert_error(login('client@test.com').post(URL, json={'description': SYMPTOM}), 429, 'llm_rate_limited')
    assert len(model.calls) == 3  # 1 intento + AI_MAX_RETRIES (2)
    assert body['details']['attempts'] == 3
    assert _ai_calls(app)[0].status == 'rate_limited'


def test_missing_api_key_returns_503_without_calling_the_provider(app, login, monkeypatch, fake_model):
    model = fake_model(fake_response({'suggestions': []}))
    monkeypatch.setitem(app.config, 'GEMINI_API_KEY', None)
    _assert_error(login('client@test.com').post(URL, json={'description': SYMPTOM}), 503, 'ai_not_configured')
    assert model.calls == []
    assert _ai_calls(app)[0].status == 'not_configured'


@pytest.mark.parametrize('outcome, code, status', [
    (api_error(400), 'llm_provider_error', 'provider_error'),
    (genai_errors.ServerError(500, {'error': {'code': 500, 'message': 'boom'}}), 'llm_provider_error',
     'provider_error'),
    (httpx.ConnectError('no network'), 'llm_provider_error', 'provider_error'),
    (fake_response('esto no es JSON'), 'invalid_llm_response', 'invalid_response'),
    (fake_response({'answer': 'sin lista de sugerencias'}), 'invalid_llm_response', 'invalid_response'),
])
def test_provider_failures_return_502(app, login, fake_model, outcome, code, status):
    fake_model(outcome)
    _assert_error(login('client@test.com').post(URL, json={'description': SYMPTOM}), 502, code)
    assert _ai_calls(app)[0].status == status


# --- Validacion, sesion y limite por usuario -------------------------------------

def test_requires_login_and_valid_body(app, login, fake_model):
    model = fake_model(fake_response({'suggestions': []}))
    _assert_error(app.test_client().post(URL, json={'description': SYMPTOM}), 401, 'unauthorized')

    client = login('client@test.com')
    body = _assert_error(client.post(URL, json={'description': 'corto', 'technique': 'magic'}), 422,
                         'validation_error')
    assert set(body['details']) == {'description', 'technique'}
    assert model.calls == []


def test_per_user_hourly_limit(app, login, monkeypatch, fake_model):
    fake_model(fake_response({'suggestions': []}))
    monkeypatch.setitem(app.config, 'AI_MAX_CALLS_PER_HOUR', 2)
    client = login('client@test.com')

    assert client.post(URL, json={'description': SYMPTOM}).status_code == 200
    assert client.post(URL, json={'description': SYMPTOM}).status_code == 200
    response = client.post(URL, json={'description': SYMPTOM})
    body = _assert_error(response, 429, 'user_quota_exceeded')
    assert 0 < int(response.headers['Retry-After']) <= 3600
    assert body['details']['retry_after_seconds'] == int(response.headers['Retry-After'])
    assert len(_ai_calls(app)) == 2  # el rechazo local no llega al proveedor

    # El limite es por usuario: otro usuario si puede
    assert login('owner@test.com').post(URL, json={'description': SYMPTOM}).status_code == 200


# --- Recuperacion y prompts (sin HTTP) ---------------------------------------------

def test_retrieval_ranks_matches_and_falls_back_to_full_catalog(app, brake_catalog):
    with app.app_context():
        assistant = app.extensions['mecatrack'].ai_assistant
        result = assistant.retrieve('no prende en las mañanas, creo que es la bateria')
        assert [s.service_id for s in result['services']][0] == 4 and not result['fallback']

        result = assistant.retrieve('quiero lavar y polichar la pintura')
        assert result['fallback'] and len(result['services']) == 4


def test_prompts_differ_only_in_technique_section():
    services = [SimpleNamespace(service_id=7, service_name='Diagnóstico con escáner', description='Codigos')]
    built = {t: prompts.build_prompt(t, 'Se prendio una luz', services) for t in prompts.TECHNIQUES}

    assert {system for system, _ in built.values()} == {prompts.SYSTEM_PROMPT}
    for _, user in built.values():
        assert '[7] Diagnóstico con escáner - Codigos' in user and 'CUSTOMER DESCRIPTION: Se prendio una luz' in user
    assert 'Example 3' in built['few_shot'][1] and 'Example' not in built['zero_shot'][1]
    assert '"reasoning"' in built['cot'][1] and '"reasoning"' not in built['zero_shot'][1]
    with pytest.raises(ValueError):
        prompts.build_prompt('tree_of_thought', 'x', services)
