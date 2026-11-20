from fastapi import FastAPI
from pydantic import BaseModel, Field

from . import concierge
from .models import ScriptedModel

app = FastAPI(title="Mecenai", version="0.1.0")
model = ScriptedModel()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": app.version}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return ChatResponse(**concierge.answer(model, req.message))
