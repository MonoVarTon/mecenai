import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, Field

import mcp_server

from . import concierge
from .models import build_model

model = build_model()

# Public MCP endpoint (streamable HTTP) for any AI assistant or agent.
_public_host = os.getenv("RENDER_EXTERNAL_HOSTNAME") or os.getenv("MECENAI_PUBLIC_HOST", "")
_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=bool(_public_host),
    allowed_hosts=[h for h in [_public_host, "localhost:*", "127.0.0.1:*"] if h],
    allowed_origins=[o for o in [f"https://{_public_host}" if _public_host else "", "http://localhost:*"] if o],
)
mcp_http = mcp_server.mcp.streamable_http_app(streamable_http_path="/", stateless_http=True,
                                              transport_security=_security)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with mcp_http.router.lifespan_context(mcp_http):
        yield


app = FastAPI(title="Mecenai", version="0.5.0", lifespan=lifespan)
app.mount("/mcp", mcp_http)

# Simple abuse protection for the public demo: per-visitor and global daily caps.
PER_MINUTE = int(os.getenv("MECENAI_PER_MINUTE", "6"))
PER_DAY_TOTAL = int(os.getenv("MECENAI_PER_DAY", "250"))
_visits: dict[str, deque] = defaultdict(deque)
_day = {"date": "", "count": 0}


def _check_limits(ip: str) -> None:
    now = time.time()
    q = _visits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    today = time.strftime("%Y-%m-%d", time.gmtime(now))
    if _day["date"] != today:
        _day.update(date=today, count=0)
    if len(q) >= PER_MINUTE or _day["count"] >= PER_DAY_TOTAL:
        raise HTTPException(429, "The demo is busy — please try again in a minute.")
    q.append(now)
    _day["count"] += 1


class Turn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=1500)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[Turn] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[str]


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": app.version}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request) -> ChatResponse:
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "?").split(",")[0]
    _check_limits(ip)
    try:
        return ChatResponse(**concierge.answer(model, req.message, [t.model_dump() for t in req.history]))
    except HTTPException:
        raise
    except Exception:  # model provider down or rate-limited: never leak details
        return ChatResponse(reply="I can't reach the concierge's model right now — please try again shortly.",
                            tool_calls=[])


@app.get("/catalog")
def catalog() -> dict:
    """Public catalogue without prices (prices only through the concierge's rules)."""
    import json
    return json.loads(mcp_server.catalog())
