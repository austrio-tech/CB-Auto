import json
from typing import Union

from fastapi import APIRouter, Depends, Header, HTTPException

from app.config import settings
from app.models.schemas import (
    AnsweredResponse,
    ChatRequest,
    DataNeededResponse,
    DataRequest,
    RespondRequest,
)
from app.services import llm
from app.services import knowledge
from app.services import session as session_store

router = APIRouter(prefix="/chat", tags=["Chat"])


async def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")


@router.post("", response_model=Union[AnsweredResponse, DataNeededResponse])
async def chat(req: ChatRequest, _=Depends(require_api_key)):
    kb = knowledge.get_relevant_kb(req.question)
    messages = [{"role": "user", "content": req.question}]

    raw = await llm.ask_llm(messages, kb)
    needs_data, payload = llm.parse_llm_response(raw)

    if needs_data:
        assert isinstance(payload, dict)
        ref_code = session_store.create_session(
            question=req.question,
            history=messages,
            data_request=payload,
            ttl_minutes=settings.session_ttl_minutes,
        )
        return DataNeededResponse(
            ref_code=ref_code,
            data_request=DataRequest(
                description=payload.get("description", ""),
                table=payload.get("table", ""),
                fields_needed=payload.get("fields_needed", []),
                filters=payload.get("filters", {}),
            ),
        )

    return AnsweredResponse(answer=str(payload))


@router.post("/respond", response_model=AnsweredResponse)
async def respond(req: RespondRequest, _=Depends(require_api_key)):
    sess = session_store.get_session(req.ref_code)
    if sess is None:
        raise HTTPException(status_code=404, detail="ref_code not found or has expired")

    kb = knowledge.get_relevant_kb(sess.question)

    # Single compact message — avoids replaying the full conversation history
    messages = [{
        "role": "user",
        "content": (
            f"Question: {sess.question}\n\n"
            f"DB data:\n{json.dumps(req.data, separators=(',', ':'))}\n\n"
            f"Answer the question using this data. Plain text only."
        ),
    }]

    raw = await llm.ask_llm(messages, kb)
    session_store.delete_session(req.ref_code)

    _, answer = llm.parse_llm_response(raw)
    return AnsweredResponse(answer=str(answer))
