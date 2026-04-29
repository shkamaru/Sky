"""
Chat endpoint — streams LLM responses for a given canvas node.
System prompt: persona + profile. Memory retrieval happens AFTER streaming
so the first token reaches the browser with minimal latency.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from db.database import get_session
from models.tables import CanvasNode, Conversation, Message
from core.llm import llm, DEFAULT_MODEL
from core.memory import (
    get_full_profile, build_profile_block,
    embed_and_store_message,
)
from core.persona import build_system_prompt
from core.similarity import detect_and_store_arrows
from pydantic import BaseModel
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    node_id: int
    message: str
    model: str = DEFAULT_MODEL


@router.post("/stream")
async def chat_stream(body: ChatRequest, session: Session = Depends(get_session)):
    node = session.get(CanvasNode, body.node_id)
    if not node or not node.conversation_id:
        raise HTTPException(status_code=404, detail="Node or conversation not found")

    # Load conversation history
    conv_messages = session.exec(
        select(Message)
        .where(Message.conversation_id == node.conversation_id)
        .order_by(Message.timestamp)
    ).all()
    is_first_message = len(conv_messages) == 0

    # Build system prompt — profile only (no memory retrieval here, keeps latency low)
    profile = get_full_profile(session)
    profile_block = build_profile_block(profile)
    system_prompt = build_system_prompt(profile_block=profile_block)

    # Assemble messages for Ollama
    messages = [{"role": "system", "content": system_prompt}]
    for msg in conv_messages:
        messages.append({
            "role": msg.role if msg.role != "agent" else "assistant",
            "content": msg.content,
        })
    messages.append({"role": "user", "content": body.message})

    # Save user message immediately
    user_msg = Message(
        conversation_id=node.conversation_id,
        role="user",
        content=body.message,
        model_used=body.model,
    )
    session.add(user_msg)

    # Auto-title node from first user message
    if is_first_message and node.title == "New conversation":
        node.title = body.message[:50].strip()
        node.updated_at = datetime.utcnow()
        session.add(node)

    session.commit()

    async def generate():
        full_response = []

        async for token in llm.chat_stream(messages=messages, model=body.model):
            full_response.append(token)
            yield token

        # ── Post-stream: save response + embed + arrows ───────────────────
        assistant_content = "".join(full_response)
        session.add(Message(
            conversation_id=node.conversation_id,
            role="assistant",
            content=assistant_content,
            model_used=body.model,
        ))
        session.commit()

        # Embed and detect related nodes only on the first message
        if is_first_message:
            embedding = await llm.embed(body.message)
            await embed_and_store_message(body.node_id, node.conversation_id, body.message)
            await detect_and_store_arrows(body.node_id, embedding, session)

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "X-Accel-Buffering": "no",       # disable nginx buffering if ever proxied
            "Cache-Control": "no-cache",
        },
    )


@router.get("/{node_id}/history")
def get_history(node_id: int, session: Session = Depends(get_session)):
    node = session.get(CanvasNode, node_id)
    if not node or not node.conversation_id:
        raise HTTPException(status_code=404, detail="Node not found")
    messages = session.exec(
        select(Message)
        .where(Message.conversation_id == node.conversation_id)
        .order_by(Message.timestamp)
    ).all()
    return {"messages": [m.model_dump() for m in messages]}
