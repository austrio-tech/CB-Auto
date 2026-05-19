from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


class RespondRequest(BaseModel):
    ref_code: str
    data: list[Any] | dict[str, Any]


class DataRequest(BaseModel):
    description: str
    table: str
    fields_needed: list[str]
    filters: dict[str, Any] = {}


class AnsweredResponse(BaseModel):
    status: Literal["answered"] = "answered"
    answer: str
    session_id: str


class DataNeededResponse(BaseModel):
    status: Literal["data_needed"] = "data_needed"
    ref_code: str
    session_id: str
    data_request: DataRequest
