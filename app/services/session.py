import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Pending data-request sessions (ref_code → question context)
# ---------------------------------------------------------------------------

@dataclass
class PendingSession:
    question: str
    conversation_history: list[dict]
    data_request: dict
    conversation_id: str
    expires_at: datetime


_pending: dict[str, PendingSession] = {}


def create_session(
    question: str,
    history: list[dict],
    data_request: dict,
    conversation_id: str,
    ttl_minutes: int = 30,
) -> str:
    ref_code = str(uuid.uuid4())
    _pending[ref_code] = PendingSession(
        question=question,
        conversation_history=history,
        data_request=data_request,
        conversation_id=conversation_id,
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
    )
    return ref_code


def get_session(ref_code: str) -> Optional[PendingSession]:
    s = _pending.get(ref_code)
    if s is None:
        return None
    if datetime.utcnow() > s.expires_at:
        del _pending[ref_code]
        return None
    return s


def delete_session(ref_code: str) -> None:
    _pending.pop(ref_code, None)


# ---------------------------------------------------------------------------
# Conversation history (session_id → rolling Q&A context)
# ---------------------------------------------------------------------------

@dataclass
class Conversation:
    history: list[dict] = field(default_factory=list)
    expires_at: datetime = field(default_factory=datetime.utcnow)


_conversations: dict[str, Conversation] = {}


def get_or_create_conversation(
    session_id: Optional[str],
    ttl_minutes: int = 30,
) -> tuple[str, list[dict]]:
    """Return (session_id, history_so_far). Creates a new conversation if needed."""
    if session_id:
        conv = _conversations.get(session_id)
        if conv and datetime.utcnow() <= conv.expires_at:
            conv.expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            return session_id, list(conv.history)

    new_id = str(uuid.uuid4())
    _conversations[new_id] = Conversation(
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes)
    )
    return new_id, []


def append_turn(
    session_id: str,
    question: str,
    answer: str,
    max_turns: int = 3,
    ttl_minutes: int = 30,
) -> None:
    """Add a completed Q&A turn to the conversation, capped at max_turns pairs."""
    conv = _conversations.get(session_id)
    if conv is None:
        return
    conv.history.append({"role": "user", "content": question})
    conv.history.append({"role": "assistant", "content": answer})
    # Keep only the most recent max_turns pairs
    if len(conv.history) > max_turns * 2:
        conv.history = conv.history[-(max_turns * 2):]
    conv.expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
