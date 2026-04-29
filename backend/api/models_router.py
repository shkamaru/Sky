from fastapi import APIRouter
from core.llm import llm

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_models():
    """Return all locally available Ollama models."""
    return {"models": llm.list_models()}
