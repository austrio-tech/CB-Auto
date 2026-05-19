import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import chat
from app.services import knowledge

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    kb = knowledge.load_knowledge_base(settings.kb_folder)
    non_empty = sum(1 for line in kb.splitlines() if line.strip())
    logger.info(f"Knowledge base ready — {non_empty} non-empty lines from '{settings.kb_folder}/'")
    yield


app = FastAPI(
    title="Business Chatbot API",
    description="Knowledge-base chatbot with on-demand database data support.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.method == "POST":
        raw = await request.body()
        body_str = raw.decode("utf-8", errors="replace")
        logger.info(f"Incoming {request.method} {request.url.path} | Body: {body_str}")
        # Re-inject body so the route handler can still read it
        async def _receive():
            return {"type": "http.request", "body": raw}
        request._receive = _receive
    return await call_next(request)

app.include_router(chat.router)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok"}
