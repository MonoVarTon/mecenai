"""Settings from environment variables, with an optional local .env file (never committed)."""
import os
from pathlib import Path


def load_env(path: Path = Path(__file__).resolve().parent.parent / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_env()

MODEL_BACKEND = os.getenv("MECENAI_MODEL", "scripted")          # scripted | groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("MECENAI_GROQ_MODEL", "qwen/qwen3.8-27b")
GROQ_URL = os.getenv("MECENAI_GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")
