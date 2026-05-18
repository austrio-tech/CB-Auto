import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Session:
    question: str
    conversation_history: list[dict]
    data_request: dict
    expires_at: datetime


_store: dict[str, Session] = {}


def create_session(
    question: str,
    history: list[dict],
    data_request: dict,
    ttl_minutes: int = 30,
) -> str:
    ref_code = str(uuid.uuid4())
    _store[ref_code] = Session(
        question=question,
        conversation_history=history,
        data_request=data_request,
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
    )
    return ref_code


def get_session(ref_code: str) -> Optional[Session]:
    session = _store.get(ref_code)
    if session is None:
        return None
    if datetime.utcnow() > session.expires_at:
        del _store[ref_code]
        return None
    return session


def delete_session(ref_code: str) -> None:
    _store.pop(ref_code, None)
