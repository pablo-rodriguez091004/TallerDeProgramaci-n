"""
Errores del asistente. Las excepciones Llm* forman parte del contrato del
puerto LlmGateway: cualquier adaptador (Gemini u otro proveedor) debe
traducir sus fallos a estas clases. `status` es el valor que se guarda en
la bitacora ai_calls.
"""


class LlmError(Exception):
    status = 'provider_error'

    def __init__(self, message, attempts=1, latency_ms=None):
        super().__init__(message)
        self.attempts = attempts
        self.latency_ms = latency_ms
        self.ai_call_id = None


class LlmNotConfigured(LlmError):
    status = 'not_configured'


class LlmTimeout(LlmError):
    status = 'timeout'


class LlmRateLimited(LlmError):
    status = 'rate_limited'


class LlmProviderError(LlmError):
    status = 'provider_error'


class InvalidModelResponse(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.ai_call_id = None


class UserQuotaExceeded(Exception):
    def __init__(self, limit, retry_after_s):
        super().__init__(f'Limit of {limit} AI calls per hour reached')
        self.limit = limit
        self.retry_after_s = retry_after_s
