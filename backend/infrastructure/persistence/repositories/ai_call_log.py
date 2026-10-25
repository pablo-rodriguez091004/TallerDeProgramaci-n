from sqlalchemy import func

from domain.ai_assistant.ports import AiCallLog
from infrastructure.persistence.extensions import db
from infrastructure.persistence.models.ai_call_model import AiCall


class SqlAlchemyAiCallLog(AiCallLog):

    def record(self, **fields):
        # Se confirma de inmediato y por separado: la bitacora debe quedar
        # aunque el resto del request falle.
        call = AiCall(**fields)
        db.session.add(call)
        db.session.commit()
        return call.ai_call_id

    def api_calls_since(self, user_id, since):
        count, oldest = (db.session.query(func.count(AiCall.ai_call_id), func.min(AiCall.created_at))
                         .filter(AiCall.user_id == user_id, AiCall.source == 'api', AiCall.created_at >= since)
                         .one())
        return count, oldest
