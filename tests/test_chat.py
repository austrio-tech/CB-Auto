import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.config import settings
from app.main import app

HEADERS = {"x-api-key": settings.api_key}


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_missing_api_key_is_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/chat", json={"question": "hello"})
    assert r.status_code in (403, 422)


@pytest.mark.asyncio
async def test_wrong_api_key_is_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/chat", json={"question": "hello"}, headers={"x-api-key": "wrong"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_chat_returns_direct_answer():
    with patch("app.services.llm.ask_llm", new=AsyncMock(return_value="Our return policy is 30 days.")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/chat", json={"question": "What is your return policy?"}, headers=HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered"
    assert "30 days" in body["answer"]


@pytest.mark.asyncio
async def test_chat_returns_data_needed():
    mock_json = '{"needs_data": true, "description": "Account balance for #1042", "fields_needed": ["balance", "due_date"]}'
    with patch("app.services.llm.ask_llm", new=AsyncMock(return_value=mock_json)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/chat", json={"question": "What is the balance on account 1042?"}, headers=HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "data_needed"
    assert "ref_code" in body
    assert body["data_request"]["fields_needed"] == ["balance", "due_date"]


@pytest.mark.asyncio
async def test_respond_with_unknown_ref_code_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/chat/respond", json={"ref_code": "does-not-exist", "data": {}}, headers=HEADERS)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_full_two_phase_flow():
    """Phase 1 returns data_needed; phase 2 with DB data returns the final answer."""
    data_needed_mock = '{"needs_data": true, "description": "Order status for #555", "fields_needed": ["status", "shipped_at"]}'
    final_answer_mock = "Order #555 has been shipped and is expected to arrive by May 20."

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        # Phase 1
        with patch("app.services.llm.ask_llm", new=AsyncMock(return_value=data_needed_mock)):
            r1 = await c.post("/chat", json={"question": "Where is my order #555?"}, headers=HEADERS)
        assert r1.status_code == 200
        assert r1.json()["status"] == "data_needed"
        ref_code = r1.json()["ref_code"]

        # Phase 2
        with patch("app.services.llm.ask_llm", new=AsyncMock(return_value=final_answer_mock)):
            r2 = await c.post(
                "/chat/respond",
                json={"ref_code": ref_code, "data": {"status": "shipped", "shipped_at": "2026-05-14"}},
                headers=HEADERS,
            )
        assert r2.status_code == 200
        assert r2.json()["status"] == "answered"
        assert "shipped" in r2.json()["answer"]


@pytest.mark.asyncio
async def test_ref_code_consumed_after_respond():
    """A ref_code cannot be reused after a successful /respond."""
    data_needed_mock = '{"needs_data": true, "description": "test", "fields_needed": ["x"]}'
    final_answer_mock = "Done."

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        with patch("app.services.llm.ask_llm", new=AsyncMock(return_value=data_needed_mock)):
            r1 = await c.post("/chat", json={"question": "test question"}, headers=HEADERS)
        ref_code = r1.json()["ref_code"]

        with patch("app.services.llm.ask_llm", new=AsyncMock(return_value=final_answer_mock)):
            await c.post("/chat/respond", json={"ref_code": ref_code, "data": {"x": 1}}, headers=HEADERS)

        # Second use of same ref_code must fail
        r3 = await c.post("/chat/respond", json={"ref_code": ref_code, "data": {"x": 1}}, headers=HEADERS)
    assert r3.status_code == 404
